import unittest
from time import sleep

from parameterized import parameterized
import os
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, MAX_TIME_TO_WAIT_FOR_IOC_TO_START, DEFAULT_IOC_START_TEXT
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
from utils.ioc_launcher import ProcServLauncher

DEVICE_PREFIX = "LINMOT_01"
DEVICE_NAME = "linmot"

# Motor record limits
MTR_LOW_LIMIT_DEFAULT = 0
MTR_HIGH_LIMIT_DEFAULT = 50
MTR_LOW_LIMIT = "MTR0101.DLLM"
MTR_HIGH_LIMIT = "MTR0101.DHLM"

# Motor movement defaults
MTR_VELOCITY_DEFAULT = 0.5
MTR_ACCELERATION_DEFAULT = 0.5

# Motor record process variables
MTR_READBACK = "MTR0101.RBV"
MTR_SETPOINT = "MTR0101.VAL"
MTR_VELOCITY = "MTR0101.VELO"
MTR_ACCELERATION = "MTR0101.ACCL"
MTR_DMOV = "MTR0101.DMOV"
MTR_STOP = "MTR0101.STOP"

# Controller state
STATE = "state"
STATE_ERROR = "Error"
STATE_MOVING = "Moving"
STATE_STOPPED = "Stopped"

# To test https://github.com/ISISComputingGroup/IBEX/issues/6423
test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motionSetPoints", "master", "settings"))

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LINMOT"),
        "macros": {
            "MTRCTRL": "1",
            "AXIS1": "yes",
            "LINMOTCONFIGDIR": test_path.replace("\\", "/"),
        },
        "emulator": DEVICE_NAME,
        "pv_for_existence": "AXIS1",
        "ioc_launcher_class": ProcServLauncher,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class LinmotTests(unittest.TestCase):
    """
    Tests for the _Device_ IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca_linmot = ChannelAccess(default_timeout=30, device_prefix="MOT")
        self._lewis.backdoor_run_function_on_device("reset")
        self.ca_linmot.assert_that_pv_exists(MTR_READBACK)
        self.check_and_reset_motor_record_limits()
        self.check_and_reset_motor_record_movement_defaults()

    def check_and_reset_motor_record_limits(self):
        """
        Check of the motor record limit values are at their expected limits. If not, then
        reset the PV to be the expected default values.
        """
        low_limit_value = self.ca_linmot.get_pv_value(MTR_LOW_LIMIT)
        if low_limit_value != MTR_LOW_LIMIT_DEFAULT:
            self.ca_linmot.set_pv_value(MTR_LOW_LIMIT, MTR_LOW_LIMIT_DEFAULT)

        high_limit_value = self.ca_linmot.get_pv_value(MTR_HIGH_LIMIT)
        if high_limit_value != MTR_HIGH_LIMIT_DEFAULT:
            self.ca_linmot.set_pv_value(MTR_HIGH_LIMIT, MTR_HIGH_LIMIT_DEFAULT)

    def check_and_reset_motor_record_movement_defaults(self):
        """
        Checks and resets the linmot motor record movement defaults that we expect
        """
        current_motor_speed = self.ca_linmot.get_pv_value(MTR_VELOCITY)
        if current_motor_speed != MTR_VELOCITY_DEFAULT:
            self.ca_linmot.set_pv_value(MTR_VELOCITY, MTR_VELOCITY_DEFAULT)

        current_motor_acceleration = self.ca_linmot.get_pv_value(MTR_ACCELERATION)
        if current_motor_acceleration != MTR_ACCELERATION_DEFAULT:
            self.ca_linmot.set_pv_value(MTR_ACCELERATION, MTR_ACCELERATION_DEFAULT)

        current_setpoint = self.ca_linmot.get_pv_value(MTR_SETPOINT)
        if current_setpoint != MTR_LOW_LIMIT_DEFAULT:
            self.ca_linmot.set_pv_value(MTR_SETPOINT, MTR_LOW_LIMIT_DEFAULT)

    @parameterized.expand([('Low limit', MTR_LOW_LIMIT_DEFAULT), ('Normal value', 12.56), ('High limit', MTR_HIGH_LIMIT_DEFAULT)])
    def test_GIVEN_motor_destination_WHEN_motor_given_destination_THEN_move_to_correct_place(self, _, target_position):
        self.ca_linmot.set_pv_value(MTR_SETPOINT, target_position)

        self.ca_linmot.assert_that_pv_is(MTR_READBACK, target_position)

    def test_GIVEN_velocity_WHEN_started_up_THEN_velocity_is_correct(self):
        # Driver converts the input velocity units mm (from the motor record) into a value the device uses.
        # See SET_VELOCITY in the devLinMot.cc driver for more information
        target_velocity_value = "0.2"
        expected_value = 104
        self.ca_linmot.set_pv_value(MTR_VELOCITY, target_velocity_value)
        self.ca_linmot.set_pv_value(MTR_SETPOINT, 10)

        self._lewis.assert_that_emulator_value_is("velocity", expected_value, timeout=5)

    def test_GIVEN_start_up_WHEN_get_motor_warn_status_THEN_it_is_correct(self):
        expected_value = 256
        device_value = self._lewis.backdoor_get_from_device("motor_warn_status_int")
        self.assertEqual(device_value, expected_value)

    @parameterized.expand([('Value 1', 0.1), ('Value 2', 0.6), ('Value 3', 2.2)])
    def test_GIVEN_new_acceleration_WHEN_set_acceleration_THEN_acceleration_set(self, _, target_acceleration):
        self.ca_linmot.set_pv_value(MTR_ACCELERATION, target_acceleration)
        self.ca_linmot.assert_that_pv_is(MTR_ACCELERATION, target_acceleration)

    def test_GIVEN_new_position_WHEN_moving_THEN_DMOVE_status_updated(self):
        expected_value = 0
        self.ca_linmot.set_pv_value(MTR_VELOCITY, 0.01)  # Slow axis so it cant reach target before stop sent
        self.ca_linmot.set_pv_value(MTR_SETPOINT, MTR_HIGH_LIMIT_DEFAULT)
        self.ca_linmot.assert_that_pv_is(MTR_DMOV, expected_value)

    def test_GIVEN_starting_up_WHEN_stopped_THEN_device_is_in_stopped_state(self):
        self._lewis.assert_that_emulator_value_is(STATE, STATE_STOPPED)

    def test_GIVEN_position_change_WHEN_move_finished_THEN_device_in_stopped_state(self):
        target_position = MTR_HIGH_LIMIT_DEFAULT
        self.ca_linmot.set_pv_value(MTR_VELOCITY, 0.05)  # Slow axis so it cant reach target before stop sent
        self.ca_linmot.set_pv_value(MTR_SETPOINT, target_position)
        self.ca_linmot.set_pv_value(MTR_STOP, 1)

        self.ca_linmot.assert_that_pv_is(MTR_DMOV, 1)

    def test_GIVEN_using_motion_set_points_and_at_non_zero_position_WHEN_ioc_restarted_THEN_emulator_does_not_move(self):
        target_position = 10
        self.ca_linmot.set_pv_value(MTR_SETPOINT, target_position)
        self.ca_linmot.assert_that_pv_is(MTR_DMOV, 1)
        self.ca_linmot.assert_that_pv_is(MTR_READBACK, target_position)

        self._ioc.start_ioc()

        self._ioc.log_file_manager.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START, DEFAULT_IOC_START_TEXT)
        self.ca.assert_that_pv_exists("AXIS1", 60)

        self.ca_linmot.assert_that_pv_is(MTR_READBACK, target_position)
