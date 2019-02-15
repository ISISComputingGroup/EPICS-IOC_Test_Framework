import unittest

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

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class NimatroTests(unittest.TestCase):
    """
    Tests for the NIMA Trough IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("CONTROL:START", timeout=30)

    def test_GIVEN_running_ioc_WHEN_set_target_area_sp_THEN_target_area_updated(self):
        expected_value = 41.15
        self.ca.set_pv_value("AREA:TARGET:SP", expected_value)

        self.ca.assert_that_pv_is("AREA:TARGET:SP:RBV", expected_value)

    def test_GIVEN_running_ioc_WHEN_set_target_pressure_sp_THEN_target_pressure_updated(self):
        expected_value = 55.6
        self.ca.set_pv_value("PRESSURE:TARGET:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE:TARGET", expected_value)

    def test_GIVEN_running_ioc_WHEN_set_target_speed_sp_THEN_target_speed_updated(self):
        expected_value = 12.0
        self.ca.set_pv_value("SPEED:SP", expected_value)

        self.ca.assert_that_pv_is("SPEED", expected_value)