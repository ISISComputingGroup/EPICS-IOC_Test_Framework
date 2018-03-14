import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "DFKPS_01"
EMULATOR_NAME = "danfysik"


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

TEST_CURRENTS = [0.4, 47, 10000]
TEST_VOLTAGES = TEST_CURRENTS

POLARITIES = ["+", "-"]


class DanfysikBase(unittest.TestCase):
    """
    Tests for danfysik.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_current_is_set_via_backdoor_WHEN_current_is_read_THEN_read_value_is_value_just_set(self):
        for curr in TEST_CURRENTS:
            self._lewis.backdoor_set_on_device("current", curr)
            self.ca.assert_that_pv_is_number("CURR", curr, tolerance=0.5)  # Tolerance 0.5 because readback is integer

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_voltage_is_set_via_backdoor_WHEN_voltage_is_read_THEN_read_value_is_value_just_set(self):
        for volt in TEST_VOLTAGES:
            self._lewis.backdoor_set_on_device("voltage", volt)
            self.ca.assert_that_pv_is_number("VOLT", volt, tolerance=0.5)  # Tolerance 0.5 because readback is integer

    def test_WHEN_polarity_setpoint_is_set_THEN_readback_updates_with_set_value(self):
        for pol in POLARITIES:
            self.ca.assert_setting_setpoint_sets_readback(pol, "POL")
