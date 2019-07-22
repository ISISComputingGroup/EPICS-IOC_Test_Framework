import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "HELIOX_01"
EMULATOR_NAME = "heliox"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HELIOX"),
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

TEST_TEMPERATURES = [0.0, 0.01, 0.333, 300]

CHANNELS = ["HE3SORB", "HE4POT", "HELOW", "HEHIGH"]


class HelioxConciseTests(unittest.TestCase):
    """
    Tests for the heliox IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_WHEN_temperature_setpoint_is_set_THEN_setpoint_readback_updates(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, set_point_pv="TEMP:SP", readback_pv="TEMP:SP:RBV")

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_WHEN_temperature_setpoint_is_set_THEN_actual_temperature_updates(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, set_point_pv="TEMP:SP", readback_pv="TEMP")

    @skip_if_recsim("Lewis backdoor is not available in recsim")
    def test_WHEN_temperature_fluctuates_between_stable_and_unstable_THEN_readback_updates(self):
        for stable in [True, False, True]:  # Check both transitions
            self._lewis.backdoor_set_on_device("temperature_stable", stable)
            self.ca.assert_that_pv_is("STABILITY", "Stable" if stable else "Unstable")
