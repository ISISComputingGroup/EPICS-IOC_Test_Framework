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
        self.ca.wait_for("CYCLES", timeout=30)
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

    def test_WHEN_device_has_been_rest_THEN_setpoint_values_match_defaults(self):
        self.ca.set_pv_value("RESET", 1)
        self.ca.assert_that_pv_is_number("SPEED:SP", DEFAULT_SPEED)
        self.ca.assert_that_pv_is_number("ACC:SP", DEFAULT_ACCELERATION)
        self.ca.assert_that_pv_is_number("WIDTH:SP", DEFAULT_WIDTH)
        self.ca.assert_that_pv_is_number("OFFSET:SP", DEFAULT_OFFSET)

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