from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.testing import skip_if_recsim, skip_if_devsim, get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister, MAX_TIME_TO_WAIT_FOR_IOC_TO_START, DEFAULT_IOC_START_TEXT
from parameterized import parameterized

# Device prefix
DEVICE_PREFIX = "DFKPS_01"
EMULATOR_NAME = "danfysik"


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

POLARITIES = ["+", "-"]
POWER_STATES = ["Off", "On"]

TEST_CURRENTS = [1.4, 47, 10000]
TEST_VOLTAGES = TEST_CURRENTS

HAS_TRIPPED = {True: "Tripped", False: "OK"}


class DanfysikBase(object):
    """
    Tests for danfysik.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=15)

        self._lewis.backdoor_run_function_on_device("reinitialise")
        self._lewis.backdoor_set_on_device("comms_initialized", True)

        # Used for daisy chained Danfysiks, default is a single Danfysik so we don't need an id
        self.id_prefixes = [""]

        self.current_readback_factor = 1

        self.set_autoonoff(False)

    def set_autoonoff(self, state):
        """
        Sets the status of the AUTOONOFF pv.

        Args:
            state (bool): True to enable AUTOONOFF, false otherwise
        """
        state_desc = "Enabled" if state else "Disabled"

        if self.ca.get_pv_value("AUTOONOFF") != state_desc:
            old_autoonoff_disp = int(self.ca.get_pv_value("AUTOONOFF.DISP"))
            self.ca.set_pv_value("AUTOONOFF.DISP", 0, wait=True, sleep_after_set=0)
            self.ca.set_pv_value("AUTOONOFF", state, sleep_after_set=0)
            self.ca.assert_that_pv_is("AUTOONOFF", state_desc)
            self.ca.set_pv_value("AUTOONOFF.DISP", old_autoonoff_disp, sleep_after_set=0)


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

    def _deactivate_interlocks(self):
        # Most danfysiks have interlocks deactivated on startup anyway
        pass

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
        self._deactivate_interlocks()
        for id_prefix in self.id_prefixes:
            self.ca.assert_that_pv_is("{}ILK".format(id_prefix), HAS_TRIPPED[False])

    @skip_if_recsim("In rec sim this test fails as recsim does not set any of the related values "
                    "which are set by the emulator")
    def test_WHEN_reset_is_sent_THEN_readbacks_and_power_are_off(self):
        for id_prefix in self.id_prefixes:
            self.ca.set_pv_value("{}CURR:SP".format(id_prefix), 5)
            self.ca.set_pv_value("{}RESET".format(id_prefix), 1)
            self.ca.assert_that_pv_is("{}POWER".format(id_prefix), "Off")
            self.ca.assert_that_pv_is("{}CURR".format(id_prefix), 0)
            self.ca.assert_that_pv_is("{}VOLT".format(id_prefix), 0)

    def test_GIVEN_power_on_and_zero_sp_WHEN_enabling_auto_onoff_THEN_device_is_powered_off(self):
        self.set_autoonoff(False)
        self.ca.set_pv_value("POWER:SP", 1)
        self.ca.set_pv_value("CURR:SP", 0)
        self.ca.assert_that_pv_is("POWER:SP", "On")

        self.set_autoonoff(True)

        self.ca.assert_that_pv_is("POWER:SP", "Off")

    def test_GIVEN_power_off_and_non_zero_sp_WHEN_enabling_auto_onoff_THEN_device_is_powered_on(self):
        self.set_autoonoff(False)
        self.ca.set_pv_value("POWER:SP", 0)
        self.ca.set_pv_value("CURR:SP", 10)
        self.ca.assert_that_pv_is("POWER:SP", "Off")

        self.set_autoonoff(True)

        self.ca.assert_that_pv_is("POWER:SP", "On")

    def test_GIVEN_power_off_and_zero_sp_WHEN_enabling_auto_onoff_THEN_device_remains_off(self):
        self.set_autoonoff(False)
        self.ca.set_pv_value("POWER:SP", 0)
        self.ca.set_pv_value("CURR:SP", 0)
        self.ca.assert_that_pv_is("POWER:SP", "Off")

        self.set_autoonoff(True)

        self.ca.assert_that_pv_is("POWER:SP", "Off")

    def test_GIVEN_power_on_and_non_zero_sp_WHEN_enabling_auto_onoff_THEN_device_remains_on(self):
        self.set_autoonoff(False)
        self.ca.set_pv_value("POWER:SP", 1)
        self.ca.set_pv_value("CURR:SP", 10)
        self.ca.assert_that_pv_is("POWER:SP", "On")

        self.set_autoonoff(True)

        self.ca.assert_that_pv_is("POWER:SP", "On")

    def test_GIVEN_power_on_and_auto_onoff_enabled_WHEN_setting_zero_value_THEN_device_is_powered_off(self):
        self.ca.set_pv_value("POWER:SP", 1)
        self.ca.set_pv_value("CURR:SP", 10)
        self.set_autoonoff(True)
        self.ca.assert_that_pv_is("POWER:SP", "On")

        self.ca.set_pv_value("CURR:SP", 0)

        self.ca.assert_that_pv_is("POWER:SP", "Off")

    def test_GIVEN_power_off_and_auto_onoff_enabled_WHEN_setting_non_zero_value_THEN_device_is_powered_on(self):
        self.set_autoonoff(True)
        self.ca.set_pv_value("POWER:SP", 0)
        self.ca.set_pv_value("CURR:SP", 0)
        self.ca.assert_that_pv_is("POWER:SP", "Off")

        self.ca.set_pv_value("CURR:SP", 10)

        self.ca.assert_that_pv_is("POWER:SP", "On")

    def test_GIVEN_auto_onoff_disabled_WHEN_sweep_to_zero_and_turn_off_triggered_THEN_actioned_by_enabling_auto_onoff_and_setting_sp_to_zero(self):
        self.set_autoonoff(False)
        self.ca.set_pv_value("POWER:SP", 1)
        self.ca.set_pv_value("CURR:SP", 10)
        self.ca.assert_that_pv_is("CURR", 10)
        self.ca.assert_that_pv_is("POWER:SP", "On")

        self.ca.set_pv_value("SWEEP_OFF", 1)

        self.ca.assert_that_pv_is("CURR", 0)
        self.ca.assert_that_pv_is("POWER:SP", "Off")

    @parameterized.expand([
        ("power_on_and_current_at_10",  True, 10),
        ("power_off_and_current_at_50", False, 50),
    ])
    @skip_if_recsim("In rec sim this test fails as there is nothing holding the device state")
    def test_WHEN_IOC_is_restarted_THEN_current_and_powered_are_not_changed(self, _, power_state, current):
        self.ca.set_pv_value("POWER:SP", int(power_state))
        self.ca.assert_that_pv_is("POWER", "On" if power_state else "Off")
        self.ca.set_pv_value("CURR:SP", current)
        self.ca.assert_that_pv_is("CURR", current)

        self._ioc.start_ioc()

        self._ioc.log_file_manager.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START, DEFAULT_IOC_START_TEXT)
        self.ca.assert_that_pv_exists("DISABLE", 60)

        self.ca.assert_that_pv_is("CURR", current)
        self.ca.assert_that_pv_is("POWER", "On" if power_state else "Off")

        self.assertEqual(str(float(current)), self._lewis.backdoor_get_from_device("absolute_current"))
        self.assertEqual(str(power_state), self._lewis.backdoor_get_from_device("power"))
