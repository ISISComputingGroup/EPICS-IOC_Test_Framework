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

    def check_write_through_python(self, addr, recordType):
        val_before = self.ca.get_pv_value(addr)
        if recordType in ["STRINGIN", "STRINGOUT", "BO", "BI", "MBBI"]:
            subprocess.call(['caput', "{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr),
                             val_before + "1"])
        else:
            subprocess.call(['caput', "{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr),
                             str(val_before + 1)])
        if val_before == self.ca.get_pv_value(addr):
            return False
        else:
            return True

    def check_write_through_cmd(self, addr, recordType):
        val_before = self.ca.get_pv_value(addr)
        FNULL = open(os.devnull, 'w')
        if recordType in ["STRINGIN", "STRINGOUT", "BO", "BI", "MBBI"]:
            subprocess.call(['caput', "{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr),
                             val_before + "1"], stdout=FNULL, stderr=subprocess.STDOUT)
        else:
            subprocess.call(['caput', "{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr),
                             str(val_before + 1)], stdout=FNULL, stderr=subprocess.STDOUT)
        if val_before == self.ca.get_pv_value(addr):
            return False
        else:
            return True

    def test_GIVEN_PV_with_disp_true_WHEN_written_to_through_python_THEN_nothing_changes(self):
        fails = []
        for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
            address = "CATEST:{}:DISP".format(recordType)
            self.ca.assert_that_pv_exists(address)
            if self.check_write_through_python(address, recordType):
                fails.append(recordType.lower())
        if fails:
            self.fail("The following record types were written to by python with DISP true:\n" + "\n".join(fails))

    def test_GIVEN_PV_with_disp_true_WHEN_written_to_through_cmd_THEN_nothing_changes(self):
        fails = []
        for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
            address = "CATEST:{}:DISP".format(recordType)
            self.ca.assert_that_pv_exists(address)
            if self.check_write_through_cmd(address, recordType):
                fails.append(recordType.lower())
        if fails:
            self.fail("The following record types were written to through caput with DISP true:\n" + "\n".join(fails))

    def test_GIVEN_PV_in_readonly_mode_WHEN_written_to_through_python_THEN_nothing_changes(self):
        fails = []
        for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
            address = "CATEST:{}:RO".format(recordType)
            self.ca.assert_that_pv_exists(address)
            if self.check_write_through_python(address, recordType):
                fails.append(recordType.lower())
        if fails:
            self.fail(
                "The following record types were written to through python in Readonly mode:\n" + "\n".join(fails))

    def test_GIVEN_PV_in_readonly_mode_WHEN_written_to_through_cmd_THEN_nothing_changes(self):
        fails = []
        for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
            address = "CATEST:{}:RO".format(recordType)
            self.ca.assert_that_pv_exists(address)
            if self.check_write_through_cmd(address, recordType):
                fails.append(recordType.lower())
        if fails:
            self.fail("The following record types were written to through caput in Readonly mode:\n" + "\n".join(fails))

    def test_GIVEN_PV_in_readonly_mode_with_disp_true_WHEN_written_to_through_python_THEN_nothing_changes(self):
        fails = []
        for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
            address = "CATEST:{}:RODISP".format(recordType)
            self.ca.assert_that_pv_exists(address)
            if self.check_write_through_python(address, recordType):
                fails.append(recordType.lower())
        if fails:
            self.fail("The following record types were written to through python in Readonly mode with disp true:\n" +
                      "\n".join(fails))

    def test_GIVEN_PV_in_readonly_mode_with_disp_true_WHEN_written_to_through_cmd_THEN_nothing_changes(self):
        fails = []
        for recordType in ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT"]:
            address = "CATEST:{}:RODISP".format(recordType)
            self.ca.assert_that_pv_exists(address)
            if self.check_write_through_python(address, recordType):
                fails.append(recordType.lower())
        if fails:
            self.fail("The following record types were written to through caput in Readonly mode with disp true:\n" +
                      "\n".join(fails))

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
