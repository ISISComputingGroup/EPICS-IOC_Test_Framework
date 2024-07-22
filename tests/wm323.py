import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "WM323_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("WM323"),
        "emulator": "wm323",
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]
SPEED_LOW_LIMIT = 3
SPEED_HIGH_LIMIT = 400


class Wm323Tests(unittest.TestCase):
    """
    Tests for the wm323 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("wm323", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)
        self.ca.assert_that_pv_exists("DISABLE")

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_WHEN_ioc_is_started_THEN_pump_type_pv_correct(self):
        self.ca.assert_that_pv_is("TYPE", "323Du")

    @parameterized.expand(
        [
            ("On low limit", SPEED_LOW_LIMIT),
            ("Intermediate value", 42),
            ("On high limit", SPEED_HIGH_LIMIT),
        ]
    )
    def test_WHEN_speed_setpoint_is_sent_THEN_readback_updates(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(value, "SPEED")

    @parameterized.expand(
        [
            ("Low limit", SPEED_LOW_LIMIT, SPEED_LOW_LIMIT - 1),
            ("High limit", SPEED_HIGH_LIMIT, SPEED_HIGH_LIMIT + 1),
        ]
    )
    def test_WHEN_speed_setpoint_is_set_outside_max_limits_THEN_setpoint_within(
        self, _, limit, value
    ):
        self.ca.set_pv_value("SPEED:SP", value)
        self.ca.assert_that_pv_is("SPEED:SP", limit)

    def test_WHEN_direction_setpoint_is_sent_THEN_readback_updates(self):
        for mode in ["Clockwise", "Anti-Clockwise"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "DIRECTION")

    def test_WHEN_status_setpoint_is_sent_THEN_readback_updates(self):
        for mode in ["Running", "Stopped"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "STATUS")

    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_pump_off_WHEN_set_pump_on_THEN_pump_turned_on(self):
        self.ca.set_pv_value("RUN:SP", "Run")

        self.ca.assert_that_pv_is("STATUS", "Running")

    @skip_if_recsim("Requires emulator logic so not supported in RECSIM")
    def test_GIVEN_pump_on_WHEN_set_pump_off_THEN_pump_paused(self):
        self.ca.set_pv_value("RUN:SP", "Run")
        self.ca.assert_that_pv_is("STATUS", "Running")

        self.ca.set_pv_value("STOP:SP", "Stop")

        self.ca.assert_that_pv_is("STATUS", "Stopped")
