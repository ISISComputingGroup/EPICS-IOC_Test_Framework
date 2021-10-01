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
test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motorExtensions", "master", "settings", "oscillatingCollimator_Wish"))

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
        ca_mot.assert_that_pv_exists("MOT:MTR0101", timeout=30)
        self.ca = ChannelAccess(device_prefix=PREFIX)
        self.ca.assert_that_pv_exists("VEL:SP", timeout=30)

    def _custom_name_func(testcase_func, param_num, param):
        return "{}_ang_{}_freq_{}_rad_{}".format(
            testcase_func.__name__,
            *param.args[0]
            )

    @parameterized.expand(
        # [(angle, frequency, radius, encoder counts per mm, full motor steps per motor rev, microsteps per motor
        # step, gearbox ratio), (expected distance, expected velocity)
        # Values confirmed via LabView VI
        [[(1.125, 0.4, 375, 200, 200, 32, 100), (2058.337, 1693.34)],
         [(2, 0.4, 375, 200, 200, 32, 100), (3760.254, 3171.962)],
         [(1.1, 0.4, 375, 200, 200, 32, 100), (2011.176, 1653.427)],
         [(1.233, 0.4, 375, 200, 200, 32, 100), (2262.922, 1867.076)],

         [(1.233, 0.4, 375, 200, 100, 32, 100), (1112.603, 903.365)],
         [(1.233, 0.4, 395, 100, 100, 32, 80), (887.295, 718.232)],
         ], testcase_func_name=_custom_name_func
    )
    def test_GIVEN_angle_frequency_and_radius_WHEN_set_THEN_distance_and_velocity_match_LabView_generated_values(self, settings, expected_values):

        # Arrange
        tolerance = 0.5

        # Act
        self.ca.set_pv_value(ANGLE, settings[0])
        self.ca.set_pv_value(FREQUENCY, settings[1])
        self.ca.set_pv_value(RADIUS, settings[2])
        self.ca.set_pv_value("ENC_COUNTS_PER_MM", settings[3])
        self.ca.set_pv_value("_STEPS_PER_REV", settings[4])
        self.ca.set_pv_value("MICROSTEPS_PER_STEP", settings[5])
        self.ca.set_pv_value("GEARBOX_RATIO", settings[6])

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

    def test_WHEN_collimator_running_THEN_thread_is_not_on_reserved_thread(self):
        # Threads 0 and 1 are reserved for homing under IBEX
        self.ca.assert_that_pv_is_not("THREAD", "0")
        self.ca.assert_that_pv_is_not("THREAD", "1")

    def test_GIVEN_number_of_cycles_to_maintenance_rotation_THEN_time_to_maintenance_cycle_is_correct(self):
        self.ca.set_pv_value(FREQUENCY, 0.4)
        self.ca.set_pv_value()