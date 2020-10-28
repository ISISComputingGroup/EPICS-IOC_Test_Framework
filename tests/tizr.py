import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import unstable_test
import os
from genie_python import genie as g


IOC_PREFIX = "TIZR_01"
DEVICE_PREFIX = g.my_pv_prefix
SIMPLE_VALUE_ONE = "TE:NDW1836:SIMPLE:VALUE1:SP"
SIMPLE_VALUE_TWO = "TE:NDW1836:SIMPLE:VALUE2"

# SIMPLE_VALUE_ONE = "TE:NDW1836:SIMPLE:VALUE:P3"
# SIMPLE_VALUE_TWO = "TE:NDW1836:SIMPLE:VALUE:P5"

# SIMPLE_VALUE_ONE = "TE:NDW1836:TIZR_01:VALUE1"
# SIMPLE_VALUE_TWO = "TE:NDW1836:TIZR_01:VALUE2"

PVONE_MAX = 100
PVTWO_MAX = 10
SAFE_VALUE = 50

PVONE_MAX = 12
PVTWO_MAX = 8
SAFE_VALUE = 11


IOCS = [
    {
        "name": IOC_PREFIX,
        "directory": get_default_ioc_dir("TIZR"),
        "macros": {
            "PVONE": SIMPLE_VALUE_ONE,
            "PVTWO": SIMPLE_VALUE_TWO,
            "PVONE_MAX": PVONE_MAX,
            "PVTWO_MAX": PVTWO_MAX,
            "SAFE_VALUE": SAFE_VALUE
        },
    },
    {
        "name": "SIMPLE",
        "directory": os.path.join(EPICS_TOP, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple"),
        "macros": {},
    }
]

SIMPLE_VALUE_ONE = "SIMPLE:VALUE1:SP"
SIMPLE_VALUE_TWO = "SIMPLE:VALUE2"
OUT_OF_RANGE_PV = "TIZR_01:OUT_OF_RANGE"

# SIMPLE_VALUE_ONE = "SIMPLE:VALUE:P3"
# SIMPLE_VALUE_TWO = "SIMPLE:VALUE:P5"

# SIMPLE_VALUE_ONE = "TIZR_01:VALUE1"
# SIMPLE_VALUE_TWO = "TIZR_01:VALUE2"

TEST_MODES = [TestModes.RECSIM]


class TiZrTests(unittest.TestCase):
    """
    Tests for the TiZr cell monitoring logic.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(IOC_PREFIX)
        self.ca = ChannelAccess(default_timeout=20)
        self.values = ["SIMPLE:VALUE1:SP", "SIMPLE:VALUE2:SP"]

        # self.ca.set_pv_value("SIMPLE:VALUE1:SP.HHSV", "NO_ALARM", sleep_after_set=0.0)
        # self.ca.set_pv_value("SIMPLE:VALUE1:SP.HSV", "NO_ALARM", sleep_after_set=0.0)
        # self.ca.set_pv_value("SIMPLE:VALUE1:SP.LLSV", "NO_ALARM", sleep_after_set=0.0)
        # self.ca.set_pv_value("SIMPLE:VALUE2.LSV", "NO_ALARM", sleep_after_set=0.0)
        # self.ca.set_pv_value("SIMPLE:VALUE2.HHSV", "NO_ALARM", sleep_after_set=0.0)
        # self.ca.set_pv_value("SIMPLE:VALUE2.HSV", "NO_ALARM", sleep_after_set=0.0)
        # self.ca.set_pv_value("SIMPLE:VALUE2.LLSV", "NO_ALARM", sleep_after_set=0.0)
        # self.ca.set_pv_value("SIMPLE:VALUE2.LSV", "NO_ALARM", sleep_after_set=0.0)

        for pv in [SIMPLE_VALUE_ONE, SIMPLE_VALUE_TWO]:
            self.ca.assert_that_pv_exists(pv)

        self.set_safe_values()

    def set_safe_values(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 0.5*PVONE_MAX)
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 0.5*PVTWO_MAX)
        self.ca.set_pv_value("TIZR_01:TIZRWARNING", 0)

    def test_GIVEN_PVONE_above_max_WHEN_PVTWO_goes_out_of_range_THEN_alarm_and_safe_value_written_to_PVONE(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 2.0*PVONE_MAX)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, 2.0*PVONE_MAX, tolerance=1e-4)

        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 2.0*PVTWO_MAX)

        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)
        # self.ca.assert_that_pv_is_number("SIMPLE:VALUE1:SP.DRVH", SAFE_VALUE, tolerance=1e-4)

        # self.ca.assert_that_pv_alarm_is("TIZR_01:WRITE_SAFE_VALUE", self.ca.Alarms.MINOR)
        # self.ca.assert_that_pv_alarm_is("TIZR_01:SET_DRVH", self.ca.Alarms.MAJOR)

        self.ca.assert_that_pv_alarm_is("TIZR_01:TIZRWARNING", self.ca.Alarms.MAJOR)
        # self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_TWO, self.ca.Alarms.MAJOR)

    def test_GIVEN_PVTWO_above_max_WHEN_PVONE_out_of_range_THEN_alarm_and_safe_value_written_to_PVONE(self):
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 2.0*PVTWO_MAX)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, 2.0*PVTWO_MAX, tolerance=1e-4)

        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 2.0*PVONE_MAX)

        # self.ca.assert_that_pv_alarm_is("TIZR_01:WRITE_SAFE_VALUE", self.ca.Alarms.MINOR)
        # self.ca.assert_that_pv_is_number("TIZR_01:WRITE_SAFE_VALUE", SAFE_VALUE, tolerance=1e-4)

        self.ca.assert_that_pv_alarm_is("TIZR_01:TIZRWARNING", self.ca.Alarms.MAJOR)

        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)
        # self.ca.assert_that_pv_alarm_is(OUT_OF_RANGE_PV, self.ca.Alarms.MAJOR)
        # self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_ONE, self.ca.Alarms.MAJOR)
        # self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_TWO, self.ca.Alarms.MAJOR)

    def test_GIVEN_PVONE_and_PVTWO_in_range_WHEN_in_range_value_written_THEN_no_alarm_and_value_written(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 0.5*PVONE_MAX)
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 0.5*PVTWO_MAX)

        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, 0.5*PVONE_MAX)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, 0.5*PVTWO_MAX)

        # self.ca.assert_that_pv_is_number("SIMPLE:VALUE1:SP.DRVH", 999999, tolerance=1e-4)

        self.ca.assert_that_pv_alarm_is("TIZR_01:TIZRWARNING", self.ca.Alarms.NONE)

        self.ca.assert_that_pv_alarm_is(OUT_OF_RANGE_PV, self.ca.Alarms.NONE)
        self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_ONE, self.ca.Alarms.NONE)
        self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_TWO, self.ca.Alarms.NONE)

        

        

    # def reset_values_to_zero(self):
    #     for val in self.values:
    #         self.ca.set_pv_value(val, 0)
    #         self.ca.assert_that_pv_is(val, 0)
    #     for val in self.values:
    #         self.ca.assert_that_pv_is(val + ".DISP", "0")

    # def test_GIVEN_both_inputs_are_zero_WHEN_setting_either_input_THEN_this_is_allowed(self):
    #     for val in self.values:
    #         self.ca.assert_that_pv_is("{}.DISP".format(val), "0")

    # @unstable_test()
    # def test_GIVEN_one_input_is_one_WHEN_setting_other_value_to_one_THEN_this_is_not_allowed(self):
    #     self.ca.set_pv_value("SIMPLE:VALUE1:SP", 1)
    #     self.ca.assert_that_pv_is("SIMPLE:VALUE1:SP", 1)
    #     # When value1 is set to non-zero, the disallowed value of value2 should be 1
    #     # i.e 'Not allowed to set this value to non-zero'
    #     self.ca.assert_that_pv_is("SIMPLE:VALUE2:SP.DISP", "1")
