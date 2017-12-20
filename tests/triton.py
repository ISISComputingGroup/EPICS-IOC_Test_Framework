import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "TRITON_01"

PID_TEST_VALUES = 0, 10**-5, 123.45, 10**5
TEMPERATURE_TEST_VALUES = 0, 10**-5, 5.4321, 1000
HEATER_RANGE_TEST_VALUES = 0.001, 0.316, 1000
HEATER_POWER_UNITS = ["A", "mA", "uA", "nA", "pA"]
VALVE_STATES = ["OPEN", "CLOSED", "NOT_FOUND"]


class TritonTests(unittest.TestCase):
    """
    Tests for the Triton IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("triton")
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skipIf(IOCRegister.uses_rec_sim, "Not implemented in recsim.")
    def test_WHEN_device_is_started_THEN_can_get_mixing_chamber_uid(self):
        self.ca.assert_that_pv_is("MC:UID", "mix_chamber_name")

    def test_WHEN_P_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "P")

    def test_WHEN_I_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "I")

    def test_WHEN_D_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "D")

    def test_WHEN_temperature_setpoint_is_set_THEN_readback_updates(self):
        for value in TEMPERATURE_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, set_point_pv="TEMP:SP", readback_pv="TEMP:SP:RBV")

    def test_WHEN_heater_range_is_set_THEN_readback_updates(self):
        for value in HEATER_RANGE_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "HEATER:RANGE")

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_heater_power(self):
        self._lewis.backdoor_set_on_device("heater_power_units", "mA")
        for value in HEATER_RANGE_TEST_VALUES:
            self._lewis.backdoor_set_on_device("heater_power", value)
            self.ca.assert_that_pv_is("HEATER:POWER", value)
            self.ca.assert_that_pv_is("HEATER:POWER.EGU", "mA")

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_heater_units_are_set_via_backdoor_THEN_egu_field_on_heater_power_updates_with_the_unit_just_set(self):
        for unit in HEATER_POWER_UNITS:
            self._lewis.backdoor_set_on_device("heater_power_units", unit)
            self.ca.assert_that_pv_is("HEATER:POWER.EGU", unit)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_closed_loop_mode_is_set_via_backdoor_THEN_the_closed_loop_pv_updates_with_value_just_set(self):
        for value in [False, True, False]:  # Need to check both transitions work properly
            self._lewis.backdoor_set_on_device("closed_loop", value)
            self.ca.assert_that_pv_is("CLOSEDLOOP", "YES" if value else "NO")

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_valve_state_is_set_via_backdoor_THEN_valve_state_pvs_update_with_value_just_set(self):
        for valve in range(1, 11):
            for valve_state_index, valve_state in enumerate(VALVE_STATES):
                self._lewis.backdoor_command(["device", "set_valve_state_backdoor", str(valve), str(valve_state_index)])
                self.ca.assert_that_pv_is("VALVES:V{}:STATE".format(valve), valve_state)

    def test_channels(self):
        for chan in range(1, 7):
            for enabled in [False, True, False]:  # Need to check both transitions work properly
                self.ca.assert_setting_setpoint_sets_readback(
                    "ON" if enabled else "OFF", "CHANNELS:T{}:STATE".format(chan))

    def test_WHEN_a_short_status_is_set_on_device_THEN_displayed_status_is_identical(self):
        # Status message that could be contained in an EPICS string type
        SHORT_STATUS = "Device status"
        assert 0 < len(SHORT_STATUS) < 40

        # Status message that device is likely to return - longer than EPICS string type but reasonable for a protocol
        MEDIUM_STATUS = "This is a device status that contains a bit more information"
        assert 40 < len(MEDIUM_STATUS) < 256

        # Short and medium statuses should be displayed in full.
        for status in [SHORT_STATUS, MEDIUM_STATUS]:
            self._lewis.backdoor_set_on_device("status", status)
            self.ca.assert_that_pv_is("STATUS", status)

    def test_WHEN_long_status_is_set_on_device_THEN_displayed_status_truncated_but_displays_at_least_500_chars(self):

        # Somewhat arbitrary, but decide on a minimum number of characters that should be displayed in a
        # status message to the user if the status message is very long. This seems to be a reasonable
        # number given the messages expected, but the manual does not provide an exhaustive list.
        minimum_characters_in_pv = 500

        # Very long status message, used to check that very long messages can be handled gracefully
        LONG_STATUS = "This device status is quite long:" + " (here is a load of information)" * 50

        assert minimum_characters_in_pv < len(LONG_STATUS)

        # Allow truncation for long status, but it should still display as many characters as possible
        self._lewis.backdoor_set_on_device("status", LONG_STATUS)
        self.ca.assert_pv_value_causes_func_to_return_true(
            "STATUS", lambda val: LONG_STATUS.startswith(val) and len(val) >= minimum_characters_in_pv)

    def test_WHEN_automation_is_set_on_device_THEN_displayed_automation_is_identical(self):
        automations = [
            "Warming up to 200K",
            "Cooling down to 1K",
        ]

        for automation in automations:
            self._lewis.backdoor_set_on_device("automation", automation)
            self.ca.assert_that_pv_is("AUTOMATION", automation)
