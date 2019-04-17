import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes


DEVICE_PREFIX = "NIMATRO_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("NIMATRO"),
        "macros": {},
    },
]

TEST_MODES = [TestModes.RECSIM]


class NimatroTests(unittest.TestCase):
    """
    Tests for the NIMA Trough IOC.

    This device uses LvDCOM and a vendor supplied driver that we are unable to test using our implementation (an
    interface to a subset of commands).

    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("CONTROL:START", timeout=30)

    @parameterized.expand([('low limit', 36), ('test_value_1', 93), ('test_value_2', 230), ('high limit', 247)])
    def test_GIVEN_running_ioc_WHEN_set_target_area_sp_THEN_target_area_updated(self, _, area):
        expected_value = area
        self.ca.set_pv_value("AREA:SP", expected_value)

        self.ca.assert_that_pv_is("AREA:SP:RBV", expected_value)

    @parameterized.expand([('low limit check', 35.0), ('high limit check', 278.0)])
    def test_GIVEN_running_ioc_WHEN_set_invalid_target_area_sp_THEN_record_bounded(self, _, area):
        expected_value = area
        self.ca.set_pv_value("AREA:SP", expected_value)

        self.ca.assert_that_pv_is_within_range("AREA:SP:RBV", 36, 247)

    @parameterized.expand([('low limit', -75.0), ('test_value_1', 10.0), ('test_value_2', 34.2), ('high limit', 75.0)])
    def test_GIVEN_running_ioc_WHEN_set_target_pressure_sp_THEN_target_pressure_updated(self, _, pressure):
        expected_value = pressure
        self.ca.set_pv_value("PRESSURE:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE:SP:RBV", expected_value)

    @parameterized.expand([('low limit check', -76.0), ('high limit check', 76.0)])
    def test_GIVEN_running_ioc_WHEN_set_invalid_target_pressure_sp_THEN_record_bounded(self, _, pressure):
        expected_value = pressure
        self.ca.set_pv_value("PRESSURE:SP", expected_value)

        self.ca.assert_that_pv_is_within_range("PRESSURE:SP", -75, 75)

    @parameterized.expand([('low limit', -174.2), ('test_value_1', -23.5), ('test_value_2', 34.2), ('high limit', 174.2)])
    def test_GIVEN_running_ioc_WHEN_set_target_speed_sp_THEN_target_speed_updated(self, _, speed):
        expected_value = speed
        self.ca.set_pv_value("SPEED:SP", expected_value)

        self.ca.assert_that_pv_is("SPEED", expected_value)

    @parameterized.expand([('low limit check', -175.0), ('high limit check', 175.0)])
    def test_GIVEN_running_ioc_WHEN_set_invalid_target_speed_sp_THEN_record_bounded(self, _, speed):
        expected_value = speed
        self.ca.set_pv_value("SPEED:SP", expected_value)

        self.ca.assert_that_pv_is_within_range("SPEED:SP:RBV", -174.2, 174.2)
