import itertools
import unittest

import six
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
TEST_HEATER_PERCENTAGES = [0.0, 0.01, 99.98, 100.0]

CHANNELS = ["HE3SORB", "HE4POT", "HELOW", "HEHIGH"]

CHANNELS_WITH_STABILITY = ["HE3SORB", "HE4POT"]

CHANNELS_WITH_HEATER_AUTO = ["HE3SORB", "HEHIGH", "HELOW"]


SKIP_SLOW_TESTS = True


class HelioxConciseTests(unittest.TestCase):
    """
    Tests for the heliox IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)
        self._lewis.backdoor_set_on_device("connected", True)

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
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.INVALID)

    @skip_if_recsim("Cannot properly simulate disconnected device in recsim")
    @unittest.skipIf(SKIP_SLOW_TESTS, "Slow test skipped")
    def test_WHEN_device_disconnected_THEN_temperature_comms_error_stays_on_for_at_least_60s_afterwards(self):
        """
        Test is slow because the logic under test is checking whether any comms errors have occured in last 120 sec.
        """
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("_TEMPERATURE_COMMS_ERROR", 0, timeout=150)
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.INVALID)
        # Should immediately indicate that there was an error
        self.ca.assert_that_pv_is("_TEMPERATURE_COMMS_ERROR", 1)
        self._lewis.backdoor_set_on_device("connected", True)
        self.ca.assert_that_pv_alarm_is("TEMP", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("_TEMPERATURE_COMMS_ERROR", 1)
        # Should stay unchanged for 120s but only assert that it doesn't change for 60 secs.
        self.ca.assert_that_pv_value_is_unchanged("_TEMPERATURE_COMMS_ERROR", wait=60)
        # Make sure it does eventually clear (within a further 150s)
        self.ca.assert_that_pv_is("_TEMPERATURE_COMMS_ERROR", 0, timeout=150)
