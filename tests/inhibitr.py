import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import unstable_test
import os
from genie_python import genie as g

test_config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "inhibitr"))


IOC_PREFIX = "INHIBITR_01"
DEVICE_PREFIX = g.my_pv_prefix
SIMPLE_VALUE_ONE = "{}SIMPLE:VALUE1:SP".format(DEVICE_PREFIX)
SIMPLE_VALUE_TWO = "{}SIMPLE:VALUE2:SP".format(DEVICE_PREFIX)

IOCS = [
    {
        "name": IOC_PREFIX,
        "directory": get_default_ioc_dir("INHIBITR"),
        "macros": {
            "ICPCONFIGROOT": test_config_path.replace("\\", "/"),
        },
    },
    {
        "name": "SIMPLE",
        "directory": os.path.join(EPICS_TOP, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple"),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM]


class InhibitrTests(unittest.TestCase):
    """
    Tests for the Inhibitr IOC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(IOC_PREFIX)
        self.ca = ChannelAccess(default_timeout=20)
        self.values = ["SIMPLE:VALUE1:SP", "SIMPLE:VALUE2:SP"]
        
        for pv in self.values:
            self.ca.assert_that_pv_exists(pv)

        self.reset_values_to_zero()

    def reset_values_to_zero(self):
        for val in self.values:
            self.ca.set_pv_value(val, 0)
            self.ca.assert_that_pv_is(val, 0)
        for val in self.values:
            self.ca.assert_that_pv_is(val + ".DISP", "0")

    def test_GIVEN_both_inputs_are_zero_WHEN_setting_either_input_THEN_this_is_allowed(self):
        for val in self.values:
            self.ca.assert_that_pv_is("{}.DISP".format(val), "0")

    @unstable_test()
    def test_GIVEN_one_input_is_one_WHEN_setting_other_value_to_one_THEN_this_is_not_allowed(self):
        self.ca.set_pv_value("SIMPLE:VALUE1:SP", 1)
        self.ca.assert_that_pv_is("SIMPLE:VALUE1:SP", 1)
        # When value1 is set to non-zero, the disallowed value of value2 should be 1
        # i.e 'Not allowed to set this value to non-zero'
        self.ca.assert_that_pv_is("SIMPLE:VALUE2:SP.DISP", "1")
