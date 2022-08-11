import itertools
import unittest
from contextlib import contextmanager

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "HELIOX_01"
EMULATOR_NAME = "heliox"

HE3POT_COARSE_TIME = 20
DRIFT_BUFFER_SIZE = 20

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HELIOX"),
        "emulator": EMULATOR_NAME,
        "macros": {
            "HE3POT_COARSE_TIME": str(HE3POT_COARSE_TIME),
            "DRIFT_BUFFER_SIZE": str(DRIFT_BUFFER_SIZE),
            "HE3SORB_NAME": "He3Sorb",
            "HE4POT_NAME": "He4Pot",
            "HEHIGH_NAME": "HeHigh",
            "HELOW_NAME": "HeLow",
        }
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

TEST_TEMPERATURES = [0.0, 0.01, 0.333, 300]
TEST_HEATER_PERCENTAGES = [0.0, 0.01, 99.98, 100.0]

CHANNELS = ["HE3SORB", "HE4POT", "HELOW", "HEHIGH"]

CHANNELS_WITH_STABILITY = ["HE3SORB", "HE4POT"]

CHANNELS_WITH_HEATER_AUTO = ["HE3SORB", "HEHIGH", "HELOW"]

# We only know some of these statuses - not an exhaustive set.
HELIOX_STATUSES = ["Low Temp", "High Temp", "Regenerate", "Shutdown"]


SKIP_SLOW_TESTS = False
slow_test = unittest.skipIf(SKIP_SLOW_TESTS, "Slow test skipped")


class HelioxTests(unittest.TestCase):
    """
    Tests for the heliox IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)
        self._lewis.backdoor_run_function_on_device("reset")

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

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_TEMPERATURES)))
    @skip_if_recsim("Lewis Backdoor not available in recsim")
    def test_WHEN_individual_channel_temperature_is_set_THEN_readback_updates(self, _, chan, temperature):
        self._lewis.backdoor_run_function_on_device("backdoor_set_channel_temperature", [chan, temperature])
        self.ca.assert_that_pv_is_number("{}:TEMP".format(chan), temperature, tolerance=0.005)

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_TEMPERATURES)))
    @skip_if_recsim("Lewis Backdoor not available in recsim")
    def test_WHEN_individual_channel_temperature_setpoint_is_set_THEN_readback_updates(self, _, chan, temperature):
        self._lewis.backdoor_run_function_on_device("backdoor_set_channel_temperature_sp", [chan, temperature])
        self.ca.assert_that_pv_is_number("{}:TEMP:SP:RBV".format(chan), temperature, tolerance=0.005)

    @parameterized.expand(parameterized_list(CHANNELS_WITH_STABILITY))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_channel_statbility_is_set_via_backdoor_THEN_readback_updates(self, _, chan):
        for stability in [True, False, True]:  # Check both transitions
            self._lewis.backdoor_run_function_on_device("backdoor_set_channel_stability", [chan, stability])
            self.ca.assert_that_pv_is("{}:STABILITY".format(chan), "Stable" if stability else "Unstable")

    @parameterized.expand(parameterized_list(CHANNELS_WITH_HEATER_AUTO))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_channel_heater_auto_is_set_via_backdoor_THEN_readback_updates(self, _, chan):
        for heater_auto in [True, False, True]:  # Check both transitions
            self._lewis.backdoor_run_function_on_device("backdoor_set_channel_heater_auto", [chan, heater_auto])
            self.ca.assert_that_pv_is("{}:HEATER:AUTO".format(chan), "On" if heater_auto else "Off")

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_HEATER_PERCENTAGES)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_individual_channel_heater_percentage_is_set_THEN_readback_updates(self, _, chan, percent):
        self._lewis.backdoor_run_function_on_device("backdoor_set_channel_heater_percent", [chan, percent])
        self.ca.assert_that_pv_is_number("{}:HEATER:PERCENT".format(chan), percent, tolerance=0.005)

    @skip_if_recsim("Cannot properly simulate disconnected device in recsim")
    def test_WHEN_device_disconnected_THEN_temperature_goes_into_alarm(self):
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.NONE)
        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.INVALID)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.NONE)

    @skip_if_recsim("Cannot properly simulate disconnected device in recsim")
    @slow_test
    def test_WHEN_device_disconnected_THEN_temperature_comms_error_stays_on_for_at_least_60s_afterwards(self):
        """
        Test is slow because the logic under test is checking whether any comms errors have occured in last 120 sec.
        """
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("REGEN:NO_RECENT_COMMS_ERROR", 1, timeout=150)
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.INVALID)
        # Should immediately indicate that there was an error
        self.ca.assert_that_pv_is("REGEN:NO_RECENT_COMMS_ERROR", 0)
        self._lewis.backdoor_set_on_device("connected", True)
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.NONE)

        # Should stay unchanged for 120s but only assert that it doesn't change for 60 secs.
        self.ca.assert_that_pv_is("REGEN:NO_RECENT_COMMS_ERROR", 0)
        self.ca.assert_that_pv_value_is_unchanged("REGEN:NO_RECENT_COMMS_ERROR", wait=60)

        # Make sure it does eventually clear (within a further 150s)
        self.ca.assert_that_pv_is("REGEN:NO_RECENT_COMMS_ERROR", 1, timeout=150)

    @contextmanager
    def _simulate_helium_3_pot_empty(self):
        """
        Simulates the helium 3 pot being empty. In this state, the he3 pot temperature will drift towards 1.5K
        regardless of the current temperature setpoint.
        """
        self._lewis.backdoor_set_on_device("helium_3_pot_empty", True)
        try:
            yield
        finally:
            self._lewis.backdoor_set_on_device("helium_3_pot_empty", False)

    @skip_if_recsim("Complex device behaviour (drifting) is not captured in recsim.")
    def test_GIVEN_helium_3_pot_is_empty_WHEN_temperature_stays_above_setpoint_for_coarse_time_THEN_regeneration_logic_detects_this(self):
        self.ca.assert_setting_setpoint_sets_readback(0.01, readback_pv="TEMP:SP:RBV", set_point_pv="TEMP:SP")
        self.ca.assert_that_pv_is("REGEN:TEMP_COARSE_CHECK", 0, timeout=(HE3POT_COARSE_TIME+10))

        with self._simulate_helium_3_pot_empty():  # Will cause temperature to drift to 1.5K
            self.ca.assert_that_pv_is("REGEN:TEMP_COARSE_CHECK", 1, timeout=(HE3POT_COARSE_TIME+10))

        self.ca.assert_that_pv_is("REGEN:TEMP_COARSE_CHECK", 0)


    @parameterized.expand(parameterized_list([0.3, 1.0, 1.234, 5.67, 12.34]))
    @skip_if_recsim("Complex device behaviour (drifting) is not captured in recsim.")
    @slow_test
    def test_GIVEN_helium_3_pot_is_empty_WHEN_drifting_THEN_drift_rate_correct(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(0.01, readback_pv="TEMP:SP:RBV", set_point_pv="TEMP:SP")

        self._lewis.backdoor_set_on_device("drift_towards", 9999999999)
        self._lewis.backdoor_set_on_device("drift_rate", value/100)  # Emulator runs at 100x speed in framework

        with self._simulate_helium_3_pot_empty():  # Will cause temperature to drift upwards continuously
            self.ca.assert_that_pv_is_number(
                "REGEN:_CALCULATE_TEMP_DRIFT.VALB", value, timeout=(DRIFT_BUFFER_SIZE+10), tolerance=0.05)
            self.ca.assert_that_pv_value_over_time_satisfies_comparator(
                "REGEN:_CALCULATE_TEMP_DRIFT.VALB", wait=DRIFT_BUFFER_SIZE,
                comparator=lambda initial, final: abs(initial - final) < 0.05 and abs(value-final) < 0.05)
            self.ca.assert_that_pv_is("REGEN:TEMP_DRIFT_RATE", 1)

        # Assert that if the temperature stops drifting the check goes false (after potentially some delay)
        self.ca.assert_that_pv_is("REGEN:TEMP_DRIFT_RATE", 0, timeout=(DRIFT_BUFFER_SIZE+10))

    @parameterized.expand(parameterized_list(HELIOX_STATUSES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_heliox_status_set_via_backdoor_THEN_status_record_updates(self, _, status):
        self._lewis.backdoor_set_on_device("status", status)
        self.ca.assert_that_pv_is("STATUS", status)

    @parameterized.expand(parameterized_list(HELIOX_STATUSES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_heliox_status_set_via_backdoor_THEN_regeneration_low_temp_status_record_updates(self, _, status):
        self._lewis.backdoor_set_on_device("status", status)
        self.ca.assert_that_pv_is("REGEN:LOW_TEMP_MODE", 1 if status == "Low Temp" else 0)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    @slow_test
    def test_WHEN_all_regeneration_conditions_are_met_THEN_regeneration_required_pv_is_true(self):
        self._lewis.backdoor_run_function_on_device("backdoor_set_channel_heater_auto", ["HE3SORB", True])
        self.ca.assert_that_pv_is("HE3SORB:HEATER:AUTO", "On")

        self._lewis.backdoor_run_function_on_device("backdoor_set_channel_heater_percent", ["HE3SORB", 0.0])
        self.ca.assert_that_pv_is("HE3SORB:HEATER:PERCENT", 0.0)

        self._lewis.backdoor_set_on_device("status", "Low Temp")
        self.ca.assert_that_pv_is("STATUS", "Low Temp")

        self.ca.assert_that_pv_is("REGEN:NO_RECENT_COMMS_ERROR", 1, timeout=150)

        self._lewis.backdoor_set_on_device("drift_towards", 9999999999)
        self._lewis.backdoor_set_on_device("drift_rate", 1.0 / 100)  # Emulator runs at 100x speed in framework

        with self._simulate_helium_3_pot_empty():
            self.ca.assert_that_pv_is("REGEN:REQUIRED", "Yes", timeout=(DRIFT_BUFFER_SIZE+10))
