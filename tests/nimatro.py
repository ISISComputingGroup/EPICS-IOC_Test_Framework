import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc


DEVICE_PREFIX = "NIMATRO_01"
DEVICE_NAME = "nimatro"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("NIMATRO"),
        "macros": {},
        "emulator": DEVICE_NAME,
    },
]

TEST_MODES = [TestModes.RECSIM]


class NimatroTests(unittest.TestCase):
    """
    Tests for the NIMA Trough IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("CONTROL:START", timeout=30)

    def test_GIVEN_running_ioc_WHEN_set_target_area_sp_THEN_target_area_updated(self):
        expected_value = 100
        self.ca.set_pv_value("AREA:SP", expected_value)

        self.ca.assert_that_pv_is("AREA", expected_value)

    def test_GIVEN_running_ioc_WHEN_set_target_pressure_sp_THEN_target_pressure_updated(self):
        expected_value = 100
        self.ca.set_pv_value("PRESSURE:SP", expected_value)

        self.ca.assert_that_pv_is("PRESSURE", expected_value)
