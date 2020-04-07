import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import IOCRegister, skip_if_recsim, get_running_lewis_and_ioc

DEVICE_PREFIX = "ROTSC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ROTSC"),
        "macros": {},
        "emulator": "rotating_sample_changer",
        "lewis_protocol": "POLARIS",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class RotscTests(unittest.TestCase):
    """
    Tests for the Rotsc IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("rotating_sample_changer", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("POSN")
        self.ca.set_pv_value("INIT", 1)
        # setting sim values required due to issue with linking INIT and SIM:INIT
        self._ioc.set_simulated_value("SIM:INIT", 1)
        self._ioc.set_simulated_value("SIM:POSN:SP", 1)

        self.ca.assert_that_pv_is("POSN", 1)

    def test_WHEN_position_set_to_value_THEN_readback_set_to_value(self):
        for val in [2, 16]:
            self.ca.assert_setting_setpoint_sets_readback(val, "POSN", "POSN:SP", val)

    @skip_if_recsim("Recsim cannot model complex behaviour (motor motion)")
    def test_GIVEN_sample_changer_is_initialised_WHEN_position_setpoint_changed_THEN_motor_active(self):
        # GIVEN
        self.ca.assert_that_pv_is("POSN", 1)
        # WHEN
        self.ca.set_pv_value("POSN:SP", 19)
        # THEN
        self.ca.assert_that_pv_is("MOTOR_0_ACTIVE", "ACTIVE")

    def test_GIVEN_current_position_WHEN_position_set_to_current_position_THEN_setpoint_not_sent(self):
        # GIVEN
        with self.ca.assert_pv_processed(self._ioc, "POSN:SP:RAW"):
            self.ca.set_pv_value("POSN:SP", 3)
            self.ca.assert_that_pv_is("POSN", 3)
            self.ca.assert_that_pv_is("STAT", "Idle")
        # WHEN
        with self.ca.assert_pv_not_processed(self._ioc, "POSN:SP:RAW"):
            self.ca.set_pv_value("POSN:SP", 3)
