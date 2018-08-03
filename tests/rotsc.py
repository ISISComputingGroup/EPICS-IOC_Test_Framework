import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import IOCRegister, skip_if_recsim


DEVICE_PREFIX = "ROTSC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ROTSC"),
        "macros": {},
        "emulator": "rotating_sample_changer",
        "emulator_protocol": "POLARIS",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class RotscTests(unittest.TestCase):
    """
    Tests for the Rotsc IOC.
    """
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("POSN")
        self.ca.set_pv_value("INIT", 1)

    def test_WHEN_position_set_to_value_THEN_readback_set_to_value(self):
        for val in [1, 16]:
            self.ca.assert_setting_setpoint_sets_readback(val, "POSN", "POSN:SP", val)

    @skip_if_recsim("Recsim cannot model complex behaviour (motor motion)")
    def test_WHEN_position_setpoint_changed_THEN_motor_active(self):
        self.ca.set_pv_value("POSN", 01)
        self.ca.set_pv_value("POSN:SP", 19)
        self.ca.assert_that_pv_is("MOTOR_0_ACTIVE", "ACTIVE")

    @skip_if_recsim("Recsim cannot model complex behaviour (motor motion)")
    def test_WHEN_position_set_to_current_position_THEN_nothing_happens(self):
        self.ca.set_pv_value("POSN", 03)
        self.ca.set_pv_value("POSN:SP", 03)
        self.ca.set_pv_value("MOTOR_0_ACTIVE", "IDLE")
