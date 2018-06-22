import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import IOCRegister


DEVICE_PREFIX = "ROTSC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ROTSC"),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM]


class RotscTests(unittest.TestCase):
    """
    Tests for the Rotsc IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("POSN")

    def test_WHEN_position_set_to_value_THEN_readback_set_to_value(self):
        for val in [1, 16]:
            self.ca.assert_setting_setpoint_sets_readback(val, "POSN", "POSN:SP", val)
