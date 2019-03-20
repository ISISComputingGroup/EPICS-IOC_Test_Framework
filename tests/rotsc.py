import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import IOCRegister, skip_if_recsim, get_running_lewis_and_ioc, assert_log_messages, \
    parameterized_list

DEVICE_PREFIX = "ROTSC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ROTSC"),
        "macros": {},
        "emulator": "rotating_sample_changer",
        "lewis_protocol": "POLARIS",
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
            self._lewis.backdoor_set_on_device("drop_sample_on_next_move", False)
            self._lewis.assert_that_emulator_value_is("drop_sample_on_next_move", "False")

        self.ca.assert_that_pv_exists("POSN")
        self.ca.set_pv_value("SEQ:MAX_MOTION_TIME", 10)  # Make faster for tests.

        self.ca.set_pv_value("INIT", 1)
        # setting sim values required due to issue with linking INIT and SIM:INIT
        self._ioc.set_simulated_value("SIM:INIT", 1)

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
        self.ca.set_pv_value("POSN:SP", 3)
        self._assert_position_reached(3)
        self.ca.assert_that_pv_is("STAT", "Idle")

        timestamp = self.ca.get_pv_value("POSN:SP:RAW.TSEL")

        # WHEN
        self.ca.set_pv_value("POSN:SP", 3)

        # THEN - check that timestamp on raw setpoint did not change i.e. did not reprocess
        self.ca.assert_that_pv_is("POSN:SP:RAW.TSEL", timestamp)
        self.ca.assert_that_pv_value_is_unchanged("POSN:SP:RAW.TSEL", wait=30)

    @skip_if_recsim("No emulator backdoor in recsim")
    def test_GIVEN_sample_changer_drops_sample_WHEN_doing_a_move_THEN_move_is_retried_and_error_in_log(self):
        self.ca.set_pv_value("POSN:SP", 1)
        self._assert_position_reached(1)

        self._lewis.backdoor_set_on_device("drop_sample_on_next_move", True)
        self._lewis.assert_that_emulator_value_is("drop_sample_on_next_move", "True")

        with assert_log_messages(self._ioc, in_time=30, must_contain="Sample arm has dropped"):
            self.ca.set_pv_value("POSN:SP", 2)

        # The move should be retried (eventually) and so the position should go correct
        self._assert_position_reached(2, timeout=60)
