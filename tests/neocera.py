import unittest
import itertools

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "NEOCERA_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("NEOCERA"),
    },
]


TEST_MODES = [TestModes.RECSIM]

SENSORS = [1, 2]
TEST_VALUES = [1.23, 456.7]


class NeoceraTests(unittest.TestCase):
    """
    Tests for the Neocera.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_units_mode_is_set_THEN_units_mode_readback_is_the_value_just_set(self):
        for mode in ["Monitor", "Control"]:
            self.ca.assert_setting_setpoint_sets_readback(mode, "MODE")

    def test_WHEN_temperatue_setpoint_is_set_THEN_readback_updates_to_the_value_just_set(self):
        for sensor, value in itertools.product(SENSORS, TEST_VALUES):
            self.ca.assert_setting_setpoint_sets_readback(
                value,
                set_point_pv="{}:TEMP:SP".format(sensor),
                readback_pv="{}:TEMP:SP:RBV".format(sensor),
            )

    def test_WHEN_pid_settings_are_set_THEN_readbacks_update_to_the_values_just_set(self):
        for sensor, value, control in itertools.product(SENSORS, TEST_VALUES, ["P", "I", "D"]):
            self.ca.assert_setting_setpoint_sets_readback(value, "{}:{}".format(sensor, control))
