import unittest
from time import sleep

import operator

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "CYBAMAN_01"
EMULATOR_DEVICE = "cybaman"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CYBAMAN"),
        "macros": {},
        "emulator": EMULATOR_DEVICE,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class CybamanTests(unittest.TestCase):
    """
    Tests for the cybaman IOC.
    """

    AXES = ["A", "B", "C"]
    test_positions = [-200, -1.23, 0, 180.0]

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_DEVICE, DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("INITIALIZE", timeout=30)

        self._lewis.backdoor_set_on_device('connected', True)

        # Check that all the relevant PVs are up.
        for axis in self.AXES:
            self.ca.assert_that_pv_exists(axis)
            self.ca.assert_that_pv_exists("{}:SP".format(axis))

        # Initialize the device, do this in setup to avoid doing it in every test
        self.ca.set_pv_value("INITIALIZE", 1)
        self.ca.assert_that_pv_is("INITIALIZED", "TRUE")

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skip_if_recsim("Uses lewis backdoor command")
    def test_WHEN_position_setpoints_are_set_via_backdoor_THEN_positions_move_towards_setpoints(self):
        for axis in self.AXES:
            for pos in self.test_positions:
                self._lewis.backdoor_set_on_device("{}_setpoint".format(axis.lower()), pos)
                self.ca.assert_that_pv_is_number("{}".format(axis), pos, tolerance=0.01)

    @skip_if_recsim("Uses lewis backdoor command")
    def test_GIVEN_home_position_is_set_WHEN_home_pv_is_set_THEN_position_moves_towards_home(self):
        for axis in self.AXES:
            for pos in self.test_positions:
                self._lewis.backdoor_set_on_device("home_position_axis_{}".format(axis.lower()), pos)
                self.ca.set_pv_value("{}:HOME".format(axis), 1)
                self.ca.assert_that_pv_is_number("{}".format(axis), pos, tolerance=0.01)

    @skip_if_recsim("Uses lewis backdoor command")
    def test_GIVEN_a_device_in_some_other_state_WHEN_reset_command_is_sent_THEN_device_is_reset_to_original_state(self):

        modifier = 12.34

        # Reset cybaman
        self.ca.set_pv_value("RESET", 1)
        self.ca.assert_that_pv_is("INITIALIZED", "FALSE")
        self.ca.set_pv_value("INITIALIZE", 1)
        self.ca.assert_that_pv_is("INITIALIZED", "TRUE")
        self.ca.assert_that_pv_value_is_unchanged("INITIALIZED", 10)

        original = {}
        for axis in self.AXES:
            original[axis] = float(self.ca.get_pv_value("{}".format(axis.upper())))

            # Set both value and setpoint to avoid the device moving back towards the setpoint
            self._lewis.backdoor_set_on_device("{}_setpoint".format(axis.lower()), original[axis] + modifier)
            self._lewis.backdoor_set_on_device("{}".format(axis.lower()), original[axis] + modifier)

            self.ca.assert_that_pv_is_number("{}".format(axis.upper()), original[axis] + modifier, tolerance=0.001)

        # Reset cybaman
        self.ca.set_pv_value("RESET", 1)

        # Check that a, b and c values are now at original values
        for axis in self.AXES:
            self.ca.assert_that_pv_is_number("{}".format(axis.upper()), original[axis], tolerance=0.001)

    def test_GIVEN_a_device_in_initialized_state_WHEN_setpoints_are_sent_THEN_device_goes_to_setpoint(self):
        for axis in self.AXES:
            for pos in self.test_positions:
                self.ca.set_pv_value("{}:SP".format(axis.upper()), pos)
                self.ca.assert_that_pv_is_number("{}".format(axis.upper()), pos)

    @skip_if_recsim("Uses lewis backdoor command")
    def test_GIVEN_a_device_with_a_setpoint_less_than_minus_150_WHEN_homed_THEN_setpoint_is_set_to_minus_150_before_home(self):
        for axis in self.AXES:
            # Ensure home position is known
            self._lewis.backdoor_set_on_device("home_position_axis_{}".format(axis.lower()), 100)

            # Ensure setpoint and readback are less than -150
            self.ca.set_pv_value("{}:SP".format(axis.upper()), -155)
            self.ca.assert_that_pv_is_number("{}".format(axis.upper()), -155, tolerance=0.01)

            # Tell axis to home
            self.ca.set_pv_value("{}:HOME".format(axis.upper()), 1)

            # Ensure that setpoint is updated to -150 before home
            self.ca.assert_that_pv_is_number("{}:SP".format(axis.upper()), -150, tolerance=0.01)

            # Let device actually reach home position
            self.ca.assert_that_pv_is_number("{}".format(axis.upper()), 100)

    @skip_if_recsim("Uses lewis backdoor command")
    def test_GIVEN_a_device_with_a_setpoint_more_than_minus_150_WHEN_homed_THEN_setpoint_is_not_set_before_home(self):
        for axis in self.AXES:
            # Ensure home position is known
            self._lewis.backdoor_set_on_device("home_position_axis_{}".format(axis.lower()), 100)

            # Ensure setpoint and readback are more than -150
            self.ca.set_pv_value("{}:SP".format(axis.upper()), -145)
            self.ca.assert_that_pv_is_number("{}".format(axis.upper()), -145, tolerance=0.01)

            # Tell axis to home
            self.ca.set_pv_value("{}:HOME".format(axis.upper()), 1)

            # Ensure that setpoint has not been updated
            self.ca.assert_that_pv_is_number("{}:SP".format(axis.upper()), -145, tolerance=0.01)

            # Let device actually reach home position
            self.ca.assert_that_pv_is_number("{}".format(axis.upper()), 100)

    def test_GIVEN_a_device_at_a_specific_position_WHEN_setpoint_is_updated_THEN_tm_val_is_calculated_correctly(self):

        test_cases = (
            # No change in setpoint, TM val should be 4000
            {"old_pos": (-1, -2, -3),  "axis_to_change": "A", "new_setpoint": -1, "expected_tm_val": 4000},
            # Test case provided from flowchart specification
            {"old_pos": (0, 0, 0),     "axis_to_change": "A", "new_setpoint": 30, "expected_tm_val": 6000},
            # Test case provided from flowchart specification
            {"old_pos": (11, -5, 102), "axis_to_change": "C", "new_setpoint": 50, "expected_tm_val": 10000},
            # Very small change, TM val should be 4000
            {"old_pos": (10, 20, 30),  "axis_to_change": "B", "new_setpoint": 21, "expected_tm_val": 4000},
        )

        for case in test_cases:
            # Ensure original position is what it's meant to be
            for axis, setpoint in zip(self.AXES, case["old_pos"]):
                self.ca.set_pv_value("{}:SP".format(axis.upper()), setpoint)
                self.ca.assert_that_pv_is_number("{}".format(axis.upper()), setpoint, tolerance=0.01)

            # Change the relevant axis to a new setpoint
            self.ca.set_pv_value("{}:SP".format(case["axis_to_change"].upper()), case["new_setpoint"])

            # Assert that the TM val calculation record contains the correct value
            # Tolerance is 1001 because rounding errors would get multiplied by 1000
            self.ca.assert_that_pv_is_number("{}:_CALC_TM_AND_SET".format(case["axis_to_change"].upper()), case["expected_tm_val"], tolerance=1001)

    def test_GIVEN_an_initialized_ioc_WHEN_reset_then_initialized_THEN_initialized_pv_is_false_then_true(self):
        self.ca.set_pv_value("RESET", 1)
        self.ca.assert_that_pv_is("INITIALIZED", "FALSE")
        self.ca.set_pv_value("INITIALIZE", 1)
        self.ca.assert_that_pv_is("INITIALIZED", "TRUE")

    def test_GIVEN_an_initialized_ioc_WHEN_stop_and_then_initialize_pvs_are_processed_THEN_initialized_pv_is_false_then_true(self):
        self.ca.set_pv_value("STOP", 1)
        self.ca.assert_that_pv_is("INITIALIZED", "FALSE")
        self.ca.set_pv_value("INITIALIZE", 1)
        self.ca.assert_that_pv_is("INITIALIZED", "TRUE")

    @skip_if_recsim("Homing not implemented in recsim")
    def test_GIVEN_one_axis_is_homed_WHEN_another_axis_has_its_setpoint_set_THEN_the_homed_axis_does_not_move(self):
        # Put all setpoints to zero
        for axis in self.AXES:
            self.ca.set_pv_value("{}:SP".format(axis.upper()), 0)
            self.ca.assert_that_pv_is("{}".format(axis.upper()), 0)

        self.ca.set_pv_value("A:HOME", 1)
        # Wait for homing to start
        sleep(2)
        # Assert that A has stopped moving (i.e. homing is finished)
        self.ca.assert_that_pv_value_is_unchanged("A", 5)
        home_position = self.ca.get_pv_value("A")

        # Modify an unrelated setpoint
        self.ca.set_pv_value("B:SP", 5)
        self.ca.assert_that_pv_is_number("B", 5, tolerance=0.01)

        # Verify that A has not changed from it's home position
        self.ca.assert_that_pv_is_number("A", home_position, tolerance=0.01)
        self.ca.assert_that_pv_value_is_unchanged("A", 5)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('RESET', ChannelAccess.Alarms.INVALID)
