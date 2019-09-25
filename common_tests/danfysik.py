from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.testing import skip_if_recsim, skip_if_devsim, get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister

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

        # Used for daisy chained Danfysiks, default is a single Danfysik so we don't need an id
        self.id_prefixes = [""]

        self.current_readback_factor = 1


class DanfysikCommon(DanfysikBase):
    def disconnect_device(self):
        """Helper method to put the device in a disconnected state, overloaded by child classes"""
        self._lewis.backdoor_set_on_device('comms_initialized', False)
        self._lewis.backdoor_set_on_device('device_available', False)

    def set_voltage(self, voltage):
        """Sets the voltage of the device, overloaded by child classes"""
        self._lewis.backdoor_set_on_device("voltage", voltage)

    def _pv_alarms_when_disconnected(self, pv):
        """Helper method to check PVs alarm when device is disconnected."""
        for id_prefix in self.id_prefixes:
            self.ca.assert_that_pv_alarm_is_not("{}{}".format(id_prefix, pv), ChannelAccess.Alarms.INVALID)
        self.disconnect_device()
        for id_prefix in self.id_prefixes:
            self.ca.assert_that_pv_alarm_is("{}{}".format(id_prefix, pv), ChannelAccess.Alarms.INVALID, timeout=10)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_voltage_pv_checked_THEN_pv_in_alarm(self):
        self._pv_alarms_when_disconnected("VOLT")

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_current_pv_checked_THEN_pv_in_alarm(self):
        self._pv_alarms_when_disconnected("CURR")

    def test_WHEN_polarity_setpoint_is_set_THEN_readback_updates_with_set_value(self):
        for id_prefix in self.id_prefixes:
            for pol in POLARITIES:
                self.ca.assert_setting_setpoint_sets_readback(pol, "{}POL".format(id_prefix))

    def test_WHEN_polarity_setpoint_is_set_with_number_THEN_readback_updates_with_set_value(self):
        for id_prefix in self.id_prefixes:
            for pol_num, pol in enumerate(POLARITIES):
                self.ca.assert_setting_setpoint_sets_readback(pol_num, "{}POL".format(id_prefix),
                                                              "{}POL:SP".format(id_prefix), pol)

    @skip_if_recsim("Recsim is not set up properly for this test to work")
    def test_WHEN_power_setpoint_is_set_THEN_readback_updates_with_set_value(self):
        for id_prefix in self.id_prefixes:
            for state in POWER_STATES:
                self.ca.assert_setting_setpoint_sets_readback(state, "{}POWER".format(id_prefix))

    @skip_if_recsim("Recsim is not set up properly for this test to work")
    def test_WHEN_power_setpoint_is_set_THEN_readback_updates_with_set_value(self):
        for id_prefix in self.id_prefixes:
            for state_num, state in enumerate(POWER_STATES):
                self.ca.assert_setting_setpoint_sets_readback(state_num, "{}POWER".format(id_prefix),
                                                              "{}POWER:SP".format(id_prefix), state)

    def test_WHEN_current_setpoint_is_set_THEN_current_readback_updates_to_set_value(self):
        for id_prefix in self.id_prefixes:
            for curr in TEST_CURRENTS:
                self.ca.set_pv_value("{}CURR:SP".format(id_prefix), curr)
                expected_value = curr*self.current_readback_factor if IOCRegister.uses_rec_sim else curr
                self.ca.assert_that_pv_is_number("{}CURR".format(id_prefix), expected_value, tolerance=0.5)  # Tolerance 0.5 because readback is integer

    @skip_if_devsim("In dev sim this test fails as the simulated records are not used")
    def test_GIVEN_emulator_not_in_use_WHEN_voltage_is_read_THEN_value_is_as_expected(self):
        expected_value = 12
        for id_prefix in self.id_prefixes:
            self.ca.set_pv_value("{}SIM:VOLT".format(id_prefix), expected_value)
            self.ca.assert_that_pv_is("{}VOLT".format(id_prefix), expected_value)

    @skip_if_recsim("Recsim is unable to simulate comms being uninitialized")
    def test_GIVEN_power_supply_comms_become_uninitialized_THEN_ioc_recovers(self):
        try:
            for volt in TEST_VOLTAGES:
                self._lewis.backdoor_set_on_device("comms_initialized", False)
                self.set_voltage(volt)
                for id_prefix in self.id_prefixes:
                    # Should be able to re-initialize comms and read the new voltage
                    self.ca.assert_that_pv_is_number("{}VOLT".format(id_prefix), volt, tolerance=0.5, timeout=30)

        finally:
            # If test fails, don't want it to affect other tests.
            self._lewis.backdoor_set_on_device("comms_initialized", True)

    def test_GIVEN_no_interlocks_active_WHEN_getting_overall_interlock_status_THEN_it_is_ok(self):
        for id_prefix in self.id_prefixes:
            self.ca.assert_that_pv_is("{}ILK".format(id_prefix), "OK")
