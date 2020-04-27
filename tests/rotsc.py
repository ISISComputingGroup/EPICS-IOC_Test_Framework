import unittest

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import (IOCRegister, skip_if_recsim, get_running_lewis_and_ioc, assert_log_messages,
                           parameterized_list)

DEVICE_PREFIX = "ROTSC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ROTSC"),
        "macros": {},
        "emulator": "rotating_sample_changer",
        "lewis_protocol": "POLARIS",
        "speed": 10,  # Slowed down from the default 100 to make sure states are reached
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class RotscTests(unittest.TestCase):
    """
    Tests for the Rotsc IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("rotating_sample_changer", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_command(["device", "reset"])
            self.ca.assert_that_pv_is("POSN", -1)  # Reset should bring us back to -1

        self.ca.set_pv_value("SEQ:MAX_MOTION_TIME", 10)  # Make faster for tests.
        self.ca.set_pv_value("SEQ:MAX_RETRY", 2)  # Make faster for tests.

        self.ca.set_pv_value("INIT", 1)
        # setting sim values required due to issue with linking INIT and SIM:INIT
        self._ioc.set_simulated_value("SIM:INIT", 1)
        self.ca.assert_that_pv_is("IS_INITIALISED", 1)

    def _assert_position_reached(self, pos, timeout=30):
        """
        Asserts that a specified position has been reached and the move is complete.

        Args:
            pos: The position to assert has been reached
        """
        self.ca.assert_that_pv_is("POSN", pos, timeout=timeout)
        if not IOCRegister.uses_rec_sim:
            # Recsim doesn't handle move finished, too complex.
            self.ca.assert_that_pv_is("CALC_MOVE_FINISHED", 1)

    # Change to various positions and check the moves all work ok.
    @parameterized.expand(parameterized_list(range(2, 16+1)))
    def test_WHEN_position_set_to_value_THEN_readback_set_to_value(self, _, val):
        self.ca.set_pv_value("POSN:SP", val)
        self._assert_position_reached(val)

    @skip_if_recsim("Recsim cannot model complex behaviour (motor motion)")
    def test_GIVEN_sample_changer_is_initialised_WHEN_position_setpoint_changed_THEN_motor_active(self):
        # GIVEN
        self._assert_position_reached(1)
        # WHEN
        self.ca.set_pv_value("POSN:SP", 19)
        # THEN
        self.ca.assert_that_pv_is("MOTOR_0_ACTIVE", "ACTIVE")

    def test_GIVEN_current_position_WHEN_position_set_to_current_position_THEN_setpoint_not_sent(self):
        # GIVEN
        with self.ca.assert_pv_processed("POSN:SP:RAW"):
            self.ca.set_pv_value("POSN:SP", 3)
            self.ca.assert_that_pv_is("POSN", 3)
            self.ca.assert_that_pv_is("STAT", "Idle")
        # WHEN
        with self.ca.assert_pv_not_processed("POSN:SP:RAW"):
            self.ca.set_pv_value("POSN:SP", 3)

    def set_up_sample_dropped_test(self, initial_position, sample_drop_position, final_position):
        # Set initial position and wait for it to get there
        self.ca.set_pv_value("POSN:SP", initial_position, wait=True)
        self._assert_position_reached(initial_position)

        # Tell emulator to drop at some point during travel
        self._lewis.backdoor_set_and_assert_set("position_to_drop_sample", sample_drop_position)

        # Move past the drop position
        self.ca.set_pv_value("POSN:SP", final_position)

        # Confirm we get a drop
        self.ca.assert_that_pv_is("ERR_LOWER", "Sample arm has dropped", timeout=10)

        # Confirm we move back to original position
        self._lewis.assert_that_emulator_value_is("sample_retrieved", str(False))
        self.ca.assert_that_pv_is("POSN", initial_position)
        self.ca.assert_that_pv_is("CALC_NOT_MOVING", 1)

    @skip_if_recsim("No emulator backdoor in recsim")
    def test_GIVEN_sample_changer_drops_sample_WHEN_doing_a_move_THEN_sample_retrieved(self):
        initial_position, sample_drop_position, final_position = 2, 5, 10
        self.set_up_sample_dropped_test(initial_position, sample_drop_position, final_position)

        # Confirm we retrieve sample and move to final position
        self._lewis.assert_that_emulator_value_is("sample_retrieved", str(True), timeout=5)
        self.ca.assert_that_pv_is("POSN", final_position)

    @skip_if_recsim("No emulator backdoor in recsim")
    def test_GIVEN_sample_changer_drops_sample_persistently_WHEN_doing_a_move_THEN_error_after_multiple_retrieves(self):
        self._lewis.backdoor_set_and_assert_set("drop_persistently", True)

        self.set_up_sample_dropped_test(3, 6, 10)

        # Confirm we eventually get an error that retrieving sample failed
        self.ca.assert_that_pv_is("ERR_STRING.SVAL", "Dropped sample could not be retrieved", timeout=60)

    @skip_if_recsim("State machine doesn't work well in recsim")
    def test_WHEN_position_set_to_value_THEN_last_position_saved(self):
        init_position = 2
        positions = [init_position, 5, 10]
        self.ca.set_pv_value("POSN:SP", init_position)
        self._assert_position_reached(init_position)

        for idx, position in enumerate(positions[1:]):
            self.ca.set_pv_value("POSN:SP", position)
            self.ca.assert_that_pv_is("LAST_POSN:SP", positions[idx])
            self._assert_position_reached(position)

    @skip_if_recsim("Moves occur instantly in recsim")
    def test_WHEN_sample_changer_goes_into_error_whilst_moving_THEN_move_not_completed(self):
        # Set initial position to 1 and wait for it to get there, so that we can tell it moved later.
        self.ca.set_pv_value("POSN:SP", 3)
        self._lewis.backdoor_set_on_device("current_err", 8)
        self.ca.assert_that_pv_is("CALC_MOVE_FINISHED", 0)
        self.ca.assert_that_pv_value_is_unchanged("CALC_MOVE_FINISHED", wait=5)
