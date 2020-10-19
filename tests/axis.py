import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes


GALIL_ADDR = "0.0.0.0"

GALIL_PREFIX = "GALIL_01"

IOCS = [
    {
        "name": GALIL_PREFIX,
        "custom_prefix": "MOT",
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "MTR0101",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "1",
        }
    }
]


TEST_MODES = [TestModes.DEVSIM]


class AxisTests(unittest.TestCase):

    def setUp(self):
        # We can use a very short timeout as all PVs are purely local and never need to wait for responses.
        self.ca = ChannelAccess(default_timeout=1, device_prefix="MOT")

    def test_GIVEN_retry_deadband_is_explicitly_set_WHEN_checking_tolerance_THEN_retry_deadband_is_used(self):
        self.ca.set_pv_value("MTR0101.MRES", 1.0, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.ERES", 1.0, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.RDBD", 123.456, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.SPDB", 0, sleep_after_set=0)

        self.ca.assert_that_pv_is("MTR0101:IN_POSITION:TOLERANCE", 123.456)

    def test_GIVEN_setpoint_deadband_is_explicitly_set_WHEN_checking_tolerance_THEN_setpoint_deadband_is_used(self):
        self.ca.set_pv_value("MTR0101.MRES", 1.0, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.ERES", 1.0, sleep_after_set=0)
        # RDBD can not be less than MRES, if it is the same as MRES that means unset
        self.ca.set_pv_value("MTR0101.RDBD", 1.0, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.SPDB", 234.567, sleep_after_set=0)

        self.ca.assert_that_pv_is("MTR0101:IN_POSITION:TOLERANCE", 234.567)

    def test_GIVEN_both_retry_deadband_and_setpoint_deadband_are_explicitly_set_WHEN_checking_tolerance_THEN_retry_deadband_is_used(self):
        self.ca.set_pv_value("MTR0101.MRES", 1.0, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.ERES", 1.0, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.RDBD", 345.678, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.SPDB", 456.789, sleep_after_set=0)

        self.ca.assert_that_pv_is("MTR0101:IN_POSITION:TOLERANCE", 345.678)

    def test_GIVEN_neither_retry_not_setpoint_deadbands_set_and_mres_bigger_than_eres_WHEN_checking_tolerance_WHEN_checking_tolerance_THEN_mres_times_ten_is_used(self):
        MRES = 456
        ERES = 123
        self.ca.set_pv_value("MTR0101.MRES", MRES, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.ERES", ERES, sleep_after_set=0)
        # RDBD can not be less than MRES, if it is the same as MRES that means unset
        self.ca.set_pv_value("MTR0101.RDBD", MRES, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.SPDB", 0, sleep_after_set=0)

        self.ca.assert_that_pv_is("MTR0101:IN_POSITION:TOLERANCE", MRES * 10)

    def test_GIVEN_neither_retry_not_setpoint_deadbands_set_and_mres_smaller_than_eres_WHEN_checking_tolerance_WHEN_checking_tolerance_THEN_eres_times_ten_is_used(self):
        MRES = 456
        ERES = 789
        self.ca.set_pv_value("MTR0101.MRES", MRES, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.ERES", ERES, sleep_after_set=0)
        # RDBD can not be less than MRES, if it is the same as MRES that means unset
        self.ca.set_pv_value("MTR0101.RDBD", MRES, sleep_after_set=0)
        self.ca.set_pv_value("MTR0101.SPDB", 0, sleep_after_set=0)

        self.ca.assert_that_pv_is("MTR0101:IN_POSITION:TOLERANCE", ERES * 10)
