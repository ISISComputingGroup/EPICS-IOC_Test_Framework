import unittest
import os
import subprocess

import itertools
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import ProcServLauncher
from utils.ioc_launcher import IOCRegister
from utils.testing import parameterized_list, unstable_test
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
PROTECTION_TYPES = ["RO", "DISP", "RODISP", ]
RECORD_TYPES = ["AO", "AI", "BO", "BI", "MBBO", "MBBI", "STRINGIN", "STRINGOUT", "CALC", "CALCOUT", ]
protection_dict = {"RO": "in READONLY ASG", "DISP": "with DISP=1", "RODISP": "in READONLY ASG with DISP=1", }

TEST_MODES = [TestModes.RECSIM, ]

# Wait 5 minutes for the IOC to come back up
MAX_TIME_TO_WAIT_FOR_IOC_TO_START = 300


def write_through_cmd(address, new_val):
    null_file = open(os.devnull, 'w')
    subprocess.call(['caput', "{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, address),
                     str(new_val)], stdout=null_file, stderr=subprocess.STDOUT)


class SimpleTests(unittest.TestCase):
    """
    Tests for the Simple IOC
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

        # Some of the ca test PVs seem to take a while to appear on build server.
        for protection, record in itertools.product(PROTECTION_TYPES, RECORD_TYPES):
            self.ca.assert_that_pv_exists("CATEST:{}:{}".format(record, protection), timeout=120)

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

    def get_toggle_value(self, address):
        """
        Gets the value of the PV and the value that will toggle it
        :return: Tuple of value before and value to toggle
        """
        val_before = self.ca.get_pv_value(address)
        return val_before, 0 if val_before == "1" or val_before == "ON" else 1

    @parameterized.expand(parameterized_list(itertools.product(PROTECTION_TYPES, RECORD_TYPES)))
    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_PV_write_protection_WHEN_written_to_through_python_THEN_nothing_changes(
            self, _, protection, record):

        def check_write_through_python(addr, record_type):
            val_before, new_val = self.get_toggle_value(addr)
            chan = CaChannelWrapper.get_chan("{}{}:{}".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr))
            try:
                if record_type in ["STRINGIN", "STRINGOUT"]:
                    chan.putw(str(new_val))
                else:
                    chan.putw(new_val)
            except CaChannelException:
                pass
            return val_before != self.ca.get_pv_value(addr)

        address = "CATEST:{}:{}".format(record, protection)
        self.ca.assert_that_pv_exists(address)
        if check_write_through_python(address, record):
            self.fail("Could (wrongly) use python to write to {} pvs {}".format(record, protection_dict[protection]))

    @parameterized.expand(parameterized_list(itertools.product(PROTECTION_TYPES, RECORD_TYPES)))
    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_PV_readonly_or_with_disp_true_WHEN_written_to_through_cmd_THEN_nothing_changes(
            self, _, protection, record):

        def check_write_through_cmd(addr):
            val_before, new_val = self.get_toggle_value(addr)
            write_through_cmd(addr, new_val)
            return val_before != self.ca.get_pv_value(addr)

        address = "CATEST:{}:{}".format(record, protection)
        self.ca.assert_that_pv_exists(address)
        if check_write_through_cmd(address):
            self.fail("Could (wrongly) use cmd to write to {} pvs {}".format(record, protection_dict[protection]))

    @parameterized.expand(parameterized_list(RECORD_TYPES))
    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_PV_in_hidden_mode_WHEN_read_attempted_THEN_get_error(self, _, record):
        address = "CATEST:{}:HIDDEN".format(record)
        self.ca.assert_that_pv_exists(address)
        try:
            self.ca.get_pv_value(address)
            self.fail("{} pv could be read in hidden mode".format(record))
        except ReadAccessException:
            pass

    @parameterized.expand(parameterized_list(itertools.product(PROTECTION_TYPES, RECORD_TYPES)))
    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_PV_in_READONLY_mode_or_with_disp_true_WHEN_linked_to_THEN_link_successful(
            self, _, protection, record):
        address = "CATEST:{}:{}".format(record, protection)
        address_out = "{}:OUT".format(address)
        self.ca.assert_that_pv_exists(address)
        val_before, new_val = self.get_toggle_value(address)
        write_through_cmd(address_out, new_val)
        if val_before == self.ca.get_pv_value(address):
            self.fail("OUT field failed to forward value to {} pvs {}".format(record, protection_dict[protection]))

    @parameterized.expand(parameterized_list(itertools.product(PROTECTION_TYPES, RECORD_TYPES)))
    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_PV_READONLY_or_with_disp_true_WHEN_told_to_process_by_python_THEN_nothing_happens(
            self, _, protection, record):

        def check_write_through_python(addr):
            chan = CaChannelWrapper.get_chan("{}{}:{}.PROC".format(os.environ["MYPVPREFIX"], DEVICE_PREFIX, addr))
            try:
                chan.putw("1")
            except CaChannelException:
                pass
            return self.ca.get_pv_value(addr + ":PROC") == "1"  # starts off as 0, goes to 1 when processed (fail)

        address = "CATEST:{}:{}".format(record, protection)
        self.ca.assert_that_pv_exists(address)
        if check_write_through_python(address):
            self.fail("Could (wrongly) use python to process protected pvs using {} pvs {}".format(
                record, protection_dict[protection]))

    @parameterized.expand(parameterized_list(itertools.product(PROTECTION_TYPES, RECORD_TYPES)))
    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_PV_READONLY_or_with_disp_true_WHEN_told_to_process_by_cmd_THEN_nothing_changes(
            self, _, protection, record):

        def check_write_through_cmd(addr):
            write_through_cmd(addr, "1")
            return self.ca.get_pv_value(addr + ":PROC") == "1"  # starts off as 0, goes to 1 when processed (fail)
            
        address = "CATEST:{}:{}".format(record, protection)
        self.ca.assert_that_pv_exists(address)
        if check_write_through_cmd(address):
            self.fail("Could (wrongly) use cmd to process protected pvs using {} pvs {}".format(
                record, protection_dict[protection]))

    def test_GIVEN_PV_WHEN_written_and_read_million_times_THEN_value_read_correctly(self):
        for i in range(1000):
            self.ca.assert_setting_setpoint_sets_readback(i, "LONG")
