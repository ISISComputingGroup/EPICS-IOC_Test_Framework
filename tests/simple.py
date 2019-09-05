import unittest
from unittest import skip
import os
import subprocess

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import ProcServLauncher
from utils.ioc_launcher import IOCRegister
from utils.testing import assert_log_messages
from utils.test_modes import TestModes
from genie_python.genie_cachannel_wrapper import CaChannelWrapper, CaChannelException
from genie_python.channel_access_exceptions import ReadAccessException

DEVICE_PREFIX = "SIMPLE"
IOC_STARTED_TEXT = "epics>"

EPICS_ROOT = os.getenv("EPICS_KIT_ROOT")

IOCS = [
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": os.path.realpath(os.path.join(EPICS_ROOT, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple")),
        "macros": {},
        "started_text": IOC_STARTED_TEXT,
    },
]

TEST_MODES = [TestModes.RECSIM, ]

# Wait 5 minutes for the IOC to come back up
MAX_TIME_TO_WAIT_FOR_IOC_TO_START = 300


class SimpleTests(unittest.TestCase):
    """
    Tests for the Simple IOC
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        self.set_auto_restart_to_true()

    def set_auto_restart_to_true(self):
        if not self._ioc.autorestart:
            self._ioc.toggle_autorestart()

    def test_GIVEN_running_ioc_in_auto_restart_mode_WHEN_ioc_crashes_THEN_ioc_reboots(self):
        # GIVEN
        self.set_auto_restart_to_true()
        self.ca.assert_that_pv_exists("DISABLE")

        # WHEN
        self.ca.set_pv_value("CRASHVALUE", "1")

        self._ioc.log_file_manager.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START, IOC_STARTED_TEXT)

        # THEN
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)


    def test_GIVEN_PV_write_protection_WHEN_written_to_through_python_THEN_nothing_changes(self):

        def check_write_through_python(addr, record_type):
            val_before = self.ca.get_pv_value(addr)
            new_val = 0 if val_before == "1" or val_before == "ON" else 1
            chan = CaChannelWrapper.get_chan("{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr))
            try:
                if record_type in ["STRINGIN", "STRINGOUT"]:
                    chan.putw(str(new_val))
                else:
                    chan.putw(new_val)
            except CaChannelException:
                pass
            if val_before == self.ca.get_pv_value(addr):
                return False
            else:
                return True

        fails = []
        for protection in ["RO", "DISP", "RODISP"]:
            for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
                address = "CATEST:{}:{}".format(recordType, protection)
                self.ca.assert_that_pv_exists(address)
                if check_write_through_python(address, recordType):
                    fails.append([recordType, protection])
        if fails:
            protectionDict = {"RO": "in READONLY ASG", "DISP": "with DISP=1", "RODISP": "in READONLY ASG with DISP=1"}
            failMsgs = ["{} {}".format(fail[0].lower(), protectionDict[fail[1]]) for fail in fails]
            self.fail("Could (wrongly) use python to write to protected using pvs with the following types and settings"
                      ":\n" + "\n".join(failMsgs))

    def test_GIVEN_PV_on_READONLY_mode_or_with_disp_true_WHEN_written_to_through_cmd_THEN_nothing_changes(self):

        def check_write_through_cmd(addr):
            val_before = self.ca.get_pv_value(addr)
            new_val = 0 if val_before == "1" or val_before == "ON" else 1
            FNULL = open(os.devnull, 'w')
            subprocess.call(['caput', "{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr),
                             str(new_val)], stdout=FNULL, stderr=subprocess.STDOUT)
            if val_before == self.ca.get_pv_value(addr):
                return False
            else:
                return True

        fails = []
        for protection in ["RO", "DISP", "RODISP"]:
            for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
                address = "CATEST:{}:{}".format(recordType, protection)
                self.ca.assert_that_pv_exists(address)
                if check_write_through_cmd(address):
                    fails.append([recordType, protection])
        if fails:
            protectionDict = {"RO": "in READONLY ASG", "DISP": "with DISP=1", "RODISP": "in READONLY ASG with DISP=1"}
            failMsgs = ["{} {}".format(fail[0].lower(), protectionDict[fail[1]]) for fail in fails]
            self.fail("Could (wrongly) use cmd to write to protected using pvs with the following types and settings"
                      ":\n" + "\n".join(failMsgs))

    def test_GIVEN_PV_in_hidden_mode_WHEN_read_attempted_THEN_get_error(self):
        fails = []
        for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
            address = "CATEST:{}:HIDDEN".format(recordType)
            self.ca.assert_that_pv_exists(address)
            try:
                self.ca.get_pv_value(address)
                fails.append(recordType.lower())
            except ReadAccessException:
                continue
        if fails:
            self.fail("The following records could be read in hidden mode:\n" + "\n".join(fails))

    def test_GIVEN_PV_in_READONLY_mode_or_with_disp_true_WHEN_linked_to_THEN_link_successful(self):
        fails = []
        for protection in ["RO", "DISP", "RODISP"]:
            for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
                address = "CATEST:{}:{}".format(recordType, protection)
                addressOut = "CATEST:{}:{}:OUT".format(recordType, protection)
                self.ca.assert_that_pv_exists(address)
                val_before = self.ca.get_pv_value(address)
                new_val = 0 if val_before == "1" or val_before == "ON" else 1
                FNULL = open(os.devnull, 'w')
                subprocess.call(['caput', "{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addressOut),
                                 str(new_val)], stdout=FNULL, stderr=subprocess.STDOUT)
                if val_before == self.ca.get_pv_value(address):
                    fails.append([recordType, protection])
        if fails:
            protectionDict = {"RO": "in READONLY ASG", "DISP": "with DISP=1", "RODISP": "in READONLY ASG with DISP=1"}
            failMsgs = ["{} {}".format(fail[0].lower(), protectionDict[fail[1]]) for fail in fails]
            self.fail("OUT field failed to forward value to pvs with the following types and settings:\n" + "\n".join(
                failMsgs))

    def test_GIVEN_PV_in_READONLY_mode_or_with_disp_true_WHEN_told_to_process_by_python_THEN_nothing_happens(self):

        def check_write_through_python(addr, record_type):
            chan = CaChannelWrapper.get_chan("{}{}:{}.PROC".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr))
            try:
                chan.putw("1")
            except CaChannelException:
                pass
            if self.ca.get_pv_value(addr + ":PROC") == "1": # starts off as 0, goes to 1 when processed (fail)
                return True
            else:
                return False

        fails = []
        for protection in ["RO", "DISP", "RODISP"]:
            for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
                address = "CATEST:{}:{}".format(recordType, protection)
                self.ca.assert_that_pv_exists(address)
                if check_write_through_python(address, recordType):
                    fails.append([recordType, protection])
        if fails:
            protectionDict = {"RO": "in READONLY ASG", "DISP": "with DISP=1", "RODISP": "in READONLY ASG with DISP=1"}
            failMsgs = ["{} {}".format(fail[0].lower(), protectionDict[fail[1]]) for fail in fails]
            self.fail("Could (wrongly) use python to process protected records using pvs with the following types and "
                      "settings:\n" + "\n".join(failMsgs))

    def test_GIVEN_PV_in_READONLY_mode_or_with_disp_true_WHEN_told_to_process_by_cmd_THEN_nothing_changes(self):

        def check_write_through_cmd(addr):
            FNULL = open(os.devnull, 'w')
            subprocess.call(['caput', "{}{}:{}.PROC".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr),
                             "1"], stdout=FNULL, stderr=subprocess.STDOUT)
            if self.ca.get_pv_value(addr + ":PROC") == "1":  # starts off as 0, goes to 1 when processed (fail)
                return True
            else:
                return False

        fails = []
        for protection in ["RO", "DISP", "RODISP"]:
            for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
                address = "CATEST:{}:{}".format(recordType, protection)
                self.ca.assert_that_pv_exists(address)
                if check_write_through_cmd(address):
                    fails.append([recordType, protection])
        if fails:
            protectionDict = {"RO": "in READONLY ASG", "DISP": "with DISP=1", "RODISP": "in READONLY ASG with DISP=1"}
            failMsgs = ["{} {}".format(fail[0].lower(), protectionDict[fail[1]]) for fail in fails]
            self.fail("Could (wrongly) use cmd to process protected records using pvs with the following types and "
                      "settings:\n" + "\n".join(failMsgs))
