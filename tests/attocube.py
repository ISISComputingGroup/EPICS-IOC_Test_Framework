import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc
from time import sleep


DEVICE_PREFIX = "ATTOCUBE_01"
EMULATOR = "attocube_anc350"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ATTOCUBE"),
        "macros": {
            "MTRCTRL": 1
        },
        "emulator": EMULATOR,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class AttocubeTests(unittest.TestCase):
    """
    Tests for the Attocube IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=None)
        self._lewis.backdoor_set_on_device('connected', True)
        self.ca.assert_that_pv_exists("MOT:MTR0101.RBV")

    def test_WHEN_moved_to_position_THEN_position_reached(self):
        position_setpoint = 5
        self.ca.set_pv_value("MOT:MTR0101", position_setpoint)
        self.ca.assert_that_pv_value_is_increasing("MOT:MTR0101.RBV", 1)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.RBV", position_setpoint, timeout=10)

    def test_GIVEN_device_not_connected_THEN_pv_in_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('MOT:MTR0101', ChannelAccess.Alarms.INVALID, timeout=60)
