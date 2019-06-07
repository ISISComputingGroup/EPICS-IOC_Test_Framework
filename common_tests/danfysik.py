from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "DFKPS_01"
EMULATOR_NAME = "danfysik"


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

POLARITIES = ["+", "-"]
POWER_STATES = ["Off", "On"]

TEST_CURRENTS = [1.4, 47, 10000]
TEST_VOLTAGES = TEST_CURRENTS


class DanfysikBase(object):
    """
    Tests for danfysik.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=15)
        self._lewis.backdoor_run_function_on_device("reset")
        self._lewis.backdoor_set_on_device("comms_initialized", True)


class DanfysikCommon(DanfysikBase):
    def _pv_alarms_when_disconnected(self, pv):
        """Helper method to check PVs alarm when device is disconnected."""
        self.ca.assert_that_pv_alarm_is_not(pv, ChannelAccess.Alarms.INVALID)
        self._lewis.backdoor_set_on_device('comms_initialized', False)
        self._lewis.backdoor_set_on_device('device_available', False)
        self.ca.assert_that_pv_alarm_is(pv, ChannelAccess.Alarms.INVALID, timeout=10)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_voltage_pv_checked_THEN_pv_in_alarm(self):
        self._pv_alarms_when_disconnected("VOLT")

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_current_pv_checked_THEN_pv_in_alarm(self):
        self._pv_alarms_when_disconnected("CURR")

    def test_WHEN_polarity_setpoint_is_set_THEN_readback_updates_with_set_value(self):
        for pol in POLARITIES:
            self.ca.assert_setting_setpoint_sets_readback(pol, "POL")

    @skip_if_recsim("Recsim is not set up properly for this test to work")
    def test_WHEN_power_setpoint_is_set_THEN_readback_updates_with_set_value(self):
        for state in POWER_STATES:
            self.ca.assert_setting_setpoint_sets_readback(state, "POWER")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_current_is_set_via_backdoor_WHEN_current_is_read_THEN_read_value_is_value_just_set(self):
        for curr in TEST_CURRENTS:
            self._lewis.backdoor_set_on_device("current", curr)
            self.ca.assert_that_pv_is_number("CURR", curr, tolerance=0.5)  # Tolerance 0.5 because readback is integer

    def test_WHEN_current_setpoint_is_set_THEN_current_readback_updates_to_set_value(self):
        for curr in TEST_CURRENTS:
            self.ca.set_pv_value("CURR:SP", curr)
            self.ca.assert_that_pv_is_number("CURR", curr, tolerance=0.5)  # Tolerance 0.5 because readback is integer

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_voltage_is_set_via_backdoor_WHEN_voltage_is_read_THEN_read_value_is_value_just_set(self):
        for volt in TEST_VOLTAGES:
            self._lewis.backdoor_set_on_device("voltage", volt)
            self.ca.assert_that_pv_is_number("VOLT", volt, tolerance=0.5)  # Tolerance 0.5 because readback is integer

    def test_GIVEN_no_interlocks_active_WHEN_getting_overall_interlock_status_THEN_it_is_ok(self):
        self.ca.assert_that_pv_is("ILK", "OK")

    @skip_if_recsim("Recsim is unable to simulate comms being uninitialized")
    def test_GIVEN_power_supply_comms_become_uninitialized_THEN_ioc_recovers(self):
        try:
            for volt in TEST_VOLTAGES:
                self._lewis.backdoor_set_on_device("comms_initialized", False)
                self._lewis.backdoor_set_on_device("voltage", volt)
                # Should be able to re-initialize comms and read the new voltage
                self.ca.assert_that_pv_is_number("VOLT", volt, tolerance=0.5, timeout=30)

        finally:
            # If test fails, don't want it to affect other tests.
            self._lewis.backdoor_set_on_device("comms_initialized", True)
