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
DEFAULT_AUTO_INITIALISE = 20000
DEFAULT_OPT_INITIALISE = 10000

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

    def reset_ioc(self):
        self.ca.set_pv_value("RESET", 1)
        # INIT:ONCE is a property held exclusively in the IOC
        calc_pv = "INIT:ONCE:CALC.CALC"
        original_calc = self.ca.get_pv_value(calc_pv)
        self.ca.set_pv_value(calc_pv, "0")
        self.ca.assert_that_pv_is("INIT:ONCE", "No")
        self.ca.set_pv_value(calc_pv, original_calc)

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("gemorc")
        self.ca = ChannelAccess(device_prefix="GEMORC_01", default_timeout=DEFAULT_TIMEOUT)
        self.ca.wait_for("ID", timeout=30)
        self.reset_ioc()
        if not IOCRegister.uses_rec_sim:
            self.reset_emulator()

        # Check setup has gone correctly
        self.check_init_state(False, False, True, False)
        self.ca.assert_that_pv_is_number("CYCLES", 0)

    def check_init_state(self, initialising, initialised, initialisation_required, oscillating):

        def bi_to_bool(val):
            return val == "Yes"

        # Do all states at once.
        match = False
        total_time = 0.0
        max_wait = DEFAULT_TIMEOUT
        interval = 1.0
        while not match and total_time < max_wait:
            actual_initialising = bi_to_bool(self.ca.get_pv_value("INIT:PROGRESS"))
            actual_initialised = bi_to_bool(self.ca.get_pv_value("INIT:DONE"))
            actual_initialisation_required = bi_to_bool(self.ca.get_pv_value("INIT:REQUIRED"))
            actual_oscillating = bi_to_bool(self.ca.get_pv_value("STAT:OSC"))

            match = all([
                initialising == actual_initialising, initialised == actual_initialised,
                initialisation_required == actual_initialisation_required, oscillating == actual_oscillating
            ])

            total_time += interval
            sleep(interval)

        try:
            self.assertTrue(match)
        except AssertionError:
            message_format = "State did not match the required state (initialising, initialised, initialisation " \
                             "required, oscillating)\nExpected: ({}, {}, {}, {})\nActual: ({}, {}, {}, {})"
            self.fail(message_format.format(
                initialising, initialised, initialisation_required, oscillating,
                actual_initialising, actual_initialised, actual_initialisation_required, actual_oscillating
            ))

    def initialise(self):
        self.ca.set_pv_value("INIT", 1)
        self.ca.assert_that_pv_is("INIT:DONE", "Yes", timeout=10)

    def start_oscillating(self):
        self.initialise()
        self.ca.set_pv_value("START", 1)

    def wait_for_re_initialisation_required(self, interval=10):
        self.ca.set_pv_value("INIT:OPT", interval)
        self.start_oscillating()
        while self.ca.get_pv_value("CYCLES") < interval:
            sleep(1)

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

    def set_and_confirm_state(self, width=None, speed=None, acceleration=None, offset=None):
        pv_value_pairs = [("WIDTH", width), ("SPEED", speed), ("ACC", acceleration), ("OFFSET", offset)]
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
        try:
            self.check_init_state(initialising=False, initialised=True, initialisation_required=False, oscillating=True)
        except AssertionError:
            raw_input("Pause...")

    def test_WHEN_settings_reset_requested_THEN_settings_return_to_default_values(self):
        settings = (
            ("WIDTH", DEFAULT_WIDTH), ("ACC", DEFAULT_ACCELERATION),
            ("SPEED",DEFAULT_SPEED), ("OFFSET", DEFAULT_OFFSET),
            ("INIT:AUTO", DEFAULT_AUTO_INITIALISE), ("INIT:OPT", DEFAULT_OPT_INITIALISE),
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

    def test_GIVEN_non_zero_offset_WHEN_re_zeroed_to_datum_THEN_offset_is_zero(self):
        self.ca.assert_that_pv_is_not_number("OFFSET", 0)
        self.ca.set_pv_value("ZERO", 1)
        self.ca.assert_that_pv_is_number("OFFSET", 0)

    def test_WHEN_auto_initialisation_interval_set_THEN_readback_matches_set_value(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_AUTO_INITIALISE+1, "INIT:AUTO")

    def test_WHEN_opt_initialisation_interval_set_THEN_readback_matches_set_value(self):
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_OPT_INITIALISE + 1, "INIT:OPT")

    @skipIf(IOCRegister.uses_rec_sim, "Cycle counting not performed in Recsim")
    def test_GIVEN_oscillating_WHEN_number_of_cycles_exceeds_optional_init_interval_THEN_initialisation_required(self):
        self.wait_for_re_initialisation_required()
        self.check_init_state(False, True, True, True)

    @skipIf(IOCRegister.uses_rec_sim, "Cycle counting not performed in Recsim")
    def test_GIVEN_initialisation_required_after_oscillating_WHEN_reinitialised_THEN_re_initialisation_not_required(self):
        self.wait_for_re_initialisation_required()
        self.ca.set_pv_value("INIT:OPT", DEFAULT_OPT_INITIALISE)
        self.initialise()
        self.check_init_state(False, True, False, True)

    @skipIf(IOCRegister.uses_rec_sim, "Initialisation logic not performed in Recsim")
    def test_WHEN_device_initialised_THEN_initialised_once(self):
        self.initialise()
        self.ca.assert_that_pv_is("INIT:ONCE", "Yes")

    @skipIf(IOCRegister.uses_rec_sim, "Initialisation logic not performed in Recsim")
    def test_WHEN_oscillating_THEN_initialised_once(self):
        self.start_oscillating()
        self.ca.assert_that_pv_is("INIT:ONCE", "Yes")

    @skipIf(IOCRegister.uses_rec_sim, "Initialisation logic not performed in Recsim")
    def test_WHEN_oscillating_and_initialisation_required_THEN_initialised_once(self):
        self.wait_for_re_initialisation_required()
        self.ca.assert_that_pv_is("INIT:ONCE", "Yes")

    @skipIf(IOCRegister.uses_rec_sim, "Initialisation logic not performed in Recsim")
    def test_WHEN_reinitialising_THEN_initialised_once(self):
        self.wait_for_re_initialisation_required()
        self.ca.set_pv_value("INIT", 1)
        self.ca.assert_that_pv_is("INIT:ONCE", "Yes")

    @skipIf(IOCRegister.uses_rec_sim, "Initialisation logic not performed in Recsim")
    def test_WHEN_reinitialised_THEN_initialised_once(self):
        self.wait_for_re_initialisation_required()
        self.initialise()
        self.ca.assert_that_pv_is("INIT:ONCE", "Yes")

    @skipIf(IOCRegister.uses_rec_sim, "Initialisation logic not performed in Recsim")
    def test_WHEN_oscillating_THEN_cycle_count_never_exceeds_auto_re_initialise_limit_for_more_than_two_seconds(self):
        initialisation_interval = 100
        self.ca.set_pv_value("INIT:AUTO", initialisation_interval)
        self.start_oscillating()

        total_wait = 0.0
        max_wait = 5*INITIALISATION_TIME
        wait_interval = 0.5
        while total_wait < max_wait:
            sleep(wait_interval)
            total_wait += wait_interval
            self.ca.assert_that_pv_is_an_integer_between("CYCLES", 0, 100, timeout=2.0)

    @skipIf(IOCRegister.uses_rec_sim, "Initialisation logic not performed in Recsim")
    def test_WHEN_oscillating_THEN_periodically_auto_initialises(self):
        initialisation_interval = 100
        self.ca.set_pv_value("INIT:AUTO", initialisation_interval)
        self.start_oscillating()
        for _ in range(2):
            self.ca.assert_that_pv_is("INIT:PROGRESS", "Yes", timeout=10*INITIALISATION_TIME)