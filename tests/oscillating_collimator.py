import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from parameterized import parameterized

import os

# IP address of device
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"

PREFIX = "MOT:OSCCOL"

# Commonly used PVs
ANGLE = "ANGLE:SP"
FREQUENCY = "FREQ:SP"
RADIUS = "RADIUS"
VELOCITY = "VEL:SP"
DISTANCE = "DIST:SP"
DISCRIMINANT = "VEL:SP:DISC:CHECK"
# The default motor resoltuion is chosen because this is reolution used when extracting the original numbers from LabView
DEFAULT_MOTOR_RESOLUTION = 0.00250

test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motorExtensions", "master", "settings", "oscillatingCollimator"))

IOCS = [
    {
        "name": "GALIL_01",
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
]

TEST_MODES = [TestModes.DEVSIM]


class OscillatingCollimatorTests(unittest.TestCase):
    """
    Tests for the LET Oscillating collimator.

    The CA.Client.Exceptions these tests generate are expected because of a workaround we had to make in the DB
    file to prevent a hang in the case of using asynFloat64 for the SP types. Issue described in ticket #2736
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        ca_mot = ChannelAccess()
        ca_mot.assert_that_pv_exists("MOT:MTR0103", timeout=30)
        ca_mot.assert_setting_setpoint_sets_readback(DEFAULT_MOTOR_RESOLUTION,
                                                     set_point_pv="MOT:MTR0103.MRES", readback_pv="MOT:MTR0103.MRES", )
        self.ca = ChannelAccess(device_prefix=PREFIX)
        self.ca.assert_that_pv_exists("VEL:SP", timeout=30)

    def _custom_name_func(testcase_func, param_num, param):
        return "{}_ang_{}_freq_{}_rad_{}".format(
            testcase_func.__name__,
            *param.args[0]
            )

    @parameterized.expand(
        # [(angle, frequency, radius), (expected distance, expected velocity)
        # Values confirmed via LabView VI
        [[(2.0, 0.5, 10.0), (281, 283)],
         [(1.0, 0.5, 10.0), (140, 140)],
         [(0.5, 0.5, 10.0), (70, 70)],
         [(2.0, 0.1, 10.0), (279, 56)],
         [(1.0, 0.1, 10.0), (140, 28)],
         [(0.5, 0.1, 10.0), (70, 14)],

         [(2.0, 0.5, 50.0), (1442, 1487)],
         [(1.0, 0.5, 50.0), (709, 719)],
         [(0.5, 0.5, 50.0), (352, 354)],

         [(2.0, 0.1, 50.0), (1398, 280)],
         [(1.0, 0.1, 50.0), (699, 140)],
         [(0.5, 0.1, 50.0), (349, 70)]], testcase_func_name=_custom_name_func
    )
    def test_GIVEN_angle_frequency_and_radius_WHEN_set_THEN_distance_and_velocity_match_LabView_generated_values(self, settings, expected_values):

        # Arrange
        tolerance = 0.5

        # Act
        # in normal operations the radius is not dynamic so set it first so it is considered in future calcs
        self.ca.set_pv_value(RADIUS, settings[2])
        self.ca.set_pv_value(ANGLE, settings[0])
        self.ca.set_pv_value(FREQUENCY, settings[1])

        # Assert
        self.ca.assert_that_pv_is_number("DIST:SP", expected_values[0], tolerance)
        self.ca.assert_that_pv_is_number("VEL:SP", expected_values[1], tolerance)

    def test_WHEN_angle_set_negative_THEN_angle_is_zero(self):
        self.ca.set_pv_value(ANGLE, -1.0)
        self.ca.assert_that_pv_is_number(ANGLE, 0.0)

    def test_WHEN_angle_set_greater_than_two_THEN_angle_is_two(self):
        self.ca.set_pv_value(ANGLE, 5.0)
        self.ca.assert_that_pv_is_number(ANGLE, 2.0)

    def test_WHEN_frequency_set_negative_THEN_angle_is_zero(self):
        self.ca.set_pv_value(FREQUENCY, -1.0)
        self.ca.assert_that_pv_is_number(FREQUENCY, 0.0)

    def test_WHEN_angle_set_greater_than_half_THEN_angle_is_half(self):
        self.ca.set_pv_value(FREQUENCY, 1.0)
        self.ca.assert_that_pv_is_number(FREQUENCY, 0.5)

    def test_WHEN_frq_set_greater_than_two_THEN_angle_is_two(self):
        self.ca.set_pv_value(ANGLE, 5.0)
        self.ca.assert_that_pv_is_number(ANGLE, 2.0)

    def test_WHEN_input_values_cause_discriminant_to_be_negative_THEN_discriminant_pv_is_one(self):

        # Act
        # in normal operations the radius is not dynamic so set it first so it is considered in future calcs
        self.ca.set_pv_value(RADIUS, 1000.0)
        self.ca.set_pv_value(ANGLE, 2.0)
        self.ca.set_pv_value(FREQUENCY, 0.5)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 1.0)

    def test_WHEN_input_values_cause_discriminant_to_be_positive_THEN_discriminant_pv_is_zero(self):

        # Act
        # in normal operations the radius is not dynamic so set it first so it is considered in future calcs
        self.ca.set_pv_value(RADIUS, 1.0)
        self.ca.set_pv_value(ANGLE, 2.0)
        self.ca.set_pv_value(FREQUENCY, 0.5)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 0.0)

    def test_WHEN_collimator_running_THEN_thread_is_not_on_reserved_thread(self):
        # Threads 0 and 1 are reserved for homing under IBEX
        self.ca.assert_that_pv_is_not("THREAD", "0")
        self.ca.assert_that_pv_is_not("THREAD", "1")
