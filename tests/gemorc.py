import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

from time import sleep

DEFAULT_WIDTH = 100
DEFAULT_OFFSET = 0
DEFAULT_SPEED = 20
DEFAULT_ACCELERATION = 500

INITIALISATION_TIME = 3
DEFAULT_TIMEOUT = 2*INITIALISATION_TIME

DEFAULT_TOLERANCE = 0.01

# Attributes: (width, speed, acceleration)
# Max lengths: (3, 2, 3)
# Max backlash, 999
# Undefined behaviour for 0 values
SETTINGS_TEST_CASES = (
    (DEFAULT_WIDTH, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    (1, 1, 1),
    (999, 99, 999),
    (1, 99, 10),
    (99, 10, 1),
    (1, 1, 999),
    (123, 45, 678),
    (987, 65, 432),
    (499, 49, 499),
)


class GemorcTests(unittest.TestCase):
    """
    Tests for the Gemorc IOC.
    """
    def reset_emulator(self):
        self._lewis.backdoor_set_on_device("reset", True)
        sleep(1)  # Wait for reset to finish so we don't jump the gun. No external indicator from emulator

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("gemorc")
        self.ca = ChannelAccess(device_prefix="GEMORC_01", default_timeout=DEFAULT_TIMEOUT)
        self.ca.wait_for("ID", timeout=30)
        if not IOCRegister.uses_rec_sim:
            self.reset_emulator()

    def check_init_state(self, initialising, initialised, initialisation_required, oscillating):
        def bool_to_yes_no(val):
            return "Yes" if val else "No"

        # Do all states at once.
        match = False
        total_time = 0.0
        max_wait = DEFAULT_TIMEOUT
        interval = 1.0
        while not match and total_time < max_wait:
            match = all([
                self.ca.get_pv_value("INIT:PROGRESS") == bool_to_yes_no(initialising),
                self.ca.get_pv_value("INIT:DONE") == bool_to_yes_no(initialised),
                self.ca.get_pv_value("INIT:REQUIRED") == bool_to_yes_no(initialisation_required),
                self.ca.get_pv_value("STAT:OSC") == bool_to_yes_no(oscillating),
                # At the moment the only case initialisation is required is it is hasn't ever been initialised
                self.ca.get_pv_value("INIT:ONCE") == bool_to_yes_no(not initialisation_required)
            ])
            total_time += interval
            sleep(interval)
        self.assertTrue(match)

    def initialise(self):
        self.ca.set_pv_value("INIT", 1)
        self.ca.assert_that_pv_is("INIT:DONE", "Yes", timeout=10)

    def start_oscillating(self):
        self.initialise()
        self.ca.set_pv_value("START", 1)

    @staticmethod
    def backlash(speed, acceleration):
        return int(0.5*speed**2/float(acceleration))

    @staticmethod
    def utility(width, backlash):
        return width/float(width+2*backlash)*100.0

    @staticmethod
    def period(width, backlash, speed):
        return (width+2*backlash)/float(speed)

    @staticmethod
    def frequency(width, backlash, speed):
        return 1.0/GemorcTests.period(width, backlash, speed)

    def set_and_confirm_state(self, width=None, speed=None, acceleration=None):
        pv_value_pairs = [("WIDTH", width), ("SPEED", speed), ("ACC", acceleration)]
        filtered_pv_values = [(pv, value) for pv, value in pv_value_pairs if value is not None]
        for pv, value in filtered_pv_values:
            self.ca.set_pv_value("{}:SP".format(pv), value)
        # Do all sets then all confirms to reduce wait time
        for pv, value in filtered_pv_values:
            self.ca.assert_that_pv_is_number(pv, value)

    def test_WHEN_width_setpoint_set_THEN_local_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_WIDTH+1, "WIDTH:SP:RBV", "WIDTH:SP")

    def test_WHEN_width_setpoint_set_THEN_remote_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_WIDTH+1, "WIDTH")

    def test_WHEN_speed_setpoint_set_THEN_local_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_SPEED+1, "SPEED:SP:RBV", "SPEED:SP")

    def test_WHEN_speed_setpoint_set_THEN_remote_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_SPEED+1, "SPEED")

    def test_WHEN_acceleration_setpoint_set_THEN_local_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_ACCELERATION+1, "ACC:SP:RBV", "ACC:SP")

    def test_WHEN_acceleration_setpoint_set_THEN_remote_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_ACCELERATION+1, "ACC")

    def test_WHEN_offset_setpoint_set_THEN_local_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_OFFSET+1, "OFFSET:SP:RBV", "OFFSET:SP")

    def test_WHEN_offset_setpoint_set_THEN_remote_readback_matches(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_OFFSET+1, "OFFSET")

    def test_WHEN_device_first_started_THEN_initialisation_required(self):
        self.check_init_state(initialising=False, initialised=False, initialisation_required=True, oscillating=False)

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_starting_state_WHEN_initialisation_requested_THEN_initialising_becomes_true(self):
        self.ca.set_pv_value("INIT", 1)
        self.check_init_state(initialising=True, initialised=False, initialisation_required=False, oscillating=False)

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_starting_state_WHEN_initialisation_requested_THEN_becomes_initialised_when_no_longer_in_progress(self):
        self.ca.set_pv_value("INIT", 1)

        total_wait = 0
        max_wait = DEFAULT_TIMEOUT
        interval = 1
        initialisation_complete = self.ca.get_pv_value("INIT:DONE")
        while self.ca.get_pv_value("INIT:PROGRESS") == "Yes" and total_wait < max_wait:
            # Always check value from before we confirmed initialisation was in progress to avoid race conditions
            self.assertNotEqual(initialisation_complete, 1)
            sleep(interval)
            total_wait += interval
            initialisation_complete = self.ca.get_pv_value("INIT:DONE")
        self.check_init_state(initialising=False, initialised=True, initialisation_required=False, oscillating=False)

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_initialised_WHEN_oscillation_requested_THEN_reports_oscillating(self):
        self.start_oscillating()
        self.ca.assert_that_pv_is("STAT:OSC", "Yes")

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_initialised_WHEN_oscillation_requested_THEN_complete_cycles_increases(self):
        self.start_oscillating()
        self.ca.assert_pv_value_is_increasing("CYCLES", DEFAULT_TIMEOUT)

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_oscillating_WHEN_oscillation_stopped_THEN_reports_not_oscillating(self):
        self.start_oscillating()
        self.ca.set_pv_value("STOP", 1)
        self.ca.assert_that_pv_is("STAT:OSC", "No")

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_initialised_WHEN_oscillation_requested_THEN_complete_cycles_does_not_change(self):
        self.start_oscillating()
        self.ca.set_pv_value("STOP", 1)
        self.ca.assert_pv_value_is_unchanged("CYCLES", DEFAULT_TIMEOUT)

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_oscillating_WHEN_initialisation_requested_THEN_initialises(self):
        self.start_oscillating()
        self.ca.set_pv_value("INIT", 1)
        self.check_init_state(initialising=True, initialised=False, initialisation_required=False, oscillating=False)

    @skipIf(IOCRegister.uses_rec_sim, "Device reset requires Lewis backdoor")
    def test_GIVEN_oscillating_and_initialisation_requested_WHEN_initialisation_complete_THEN_resumes_oscillation(self):
        self.start_oscillating()
        self.initialise()
        self.check_init_state(initialising=False, initialised=True, initialisation_required=False, oscillating=True)

    def test_WHEN_settings_reset_requested_THEN_settings_return_to_default_values(self):
        settings = (
            ("WIDTH", DEFAULT_WIDTH), ("ACC", DEFAULT_ACCELERATION), ("SPEED",DEFAULT_SPEED), ("OFFSET", DEFAULT_OFFSET)
        )
        for pv, default in settings:
            self.ca.set_pv_value("{}:SP".format(pv), default+1)  # I prefer the two lines here
            self.ca.assert_that_pv_is_not_number(pv, default)

        self.ca.set_pv_value("RESET", 1)

        for pv, default in settings:
            self.ca.assert_that_pv_is_number(pv, default)

    @skipIf(IOCRegister.uses_rec_sim, "Calculation logic not performed in Recsim")
    def test_WHEN_device_is_running_THEN_it_gets_PnP_identity_from_emulator(self):
        self.ca.assert_that_pv_is("ID", "IBEX_GEMORC_DEVICE_EMULATOR", timeout=20)  # On a very slow scan

    def test_GIVEN_standard_test_cases_WHEN_backlash_calculated_locally_THEN_result_is_in_range_supported_by_device(self):
        for _, speed, acceleration in SETTINGS_TEST_CASES:
            self.assertTrue(0 <= self.backlash(speed, acceleration) <= 999)

    @skipIf(IOCRegister.uses_rec_sim, "Depends on emulator value")
    def test_WHEN_emulator_running_THEN_backlash_has_value_derived_from_speed_and_acceleration(self):
        for width, speed, acceleration in SETTINGS_TEST_CASES:
            self.set_and_confirm_state(speed=speed, acceleration=acceleration)
            self.ca.assert_that_pv_is_number("BACKLASH", self.backlash(speed, acceleration))

    def test_GIVEN_non_zero_speed_WHEN_width_and_speed_set_THEN_utility_time_corresponds_to_formula_in_test(self):
        for width, speed, acceleration in SETTINGS_TEST_CASES:
            self.set_and_confirm_state(width, speed, acceleration)
            backlash = self.ca.get_pv_value("BACKLASH")
            self.ca.assert_that_pv_is_number("UTILITY", self.utility(width, backlash), tolerance=DEFAULT_TOLERANCE)

    def test_WHEN_emulator_running_THEN_period_has_value_as_derived_from_speed_width_and_backlash(self):
        for width, speed, acceleration in SETTINGS_TEST_CASES:
            self.set_and_confirm_state(width, speed, acceleration)
            backlash = self.ca.get_pv_value("BACKLASH")
            self.ca.assert_that_pv_is_number("PERIOD", self.period(width, backlash, speed), tolerance=DEFAULT_TOLERANCE)

    def test_WHEN_emulator_running_THEN_frequency_has_value_as_derived_from_speed_width_and_backlash(self):
        for width, speed, acceleration in SETTINGS_TEST_CASES:
            self.set_and_confirm_state(width, speed, acceleration)
            backlash = self.ca.get_pv_value("BACKLASH")
            self.ca.assert_that_pv_is_number("FREQ", self.frequency(width, backlash, speed), tolerance=DEFAULT_TOLERANCE)
