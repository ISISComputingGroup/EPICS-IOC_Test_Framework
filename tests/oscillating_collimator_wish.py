import unittest
from common_tests.oscillating_collimators import OscillatingCollimatorBase, _custom_name_func, ANGLE, FREQUENCY, RADIUS, \
    GALIL_ADDR, PREFIX
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from parameterized import parameterized
import os
from utils.test_modes import TestModes

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


class OscillatingCollimatorTests(OscillatingCollimatorBase, unittest.TestCase):
    """
    Tests for the WISH Oscillating collimator.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        ca_mot = ChannelAccess()
        ca_mot.assert_that_pv_exists("MOT:MTR0101", timeout=30)
        self.ca = ChannelAccess(device_prefix=PREFIX, default_wait_time=0)
        self.ca.assert_that_pv_exists("VEL:SP", timeout=30)

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

    def test_GIVEN_number_of_cycles_to_maintenance_rotation_THEN_time_to_maintenance_cycle_is_correct(self):
        freq = 0.4
        maintenance_cycles_before_rotation = 5000
        current_cycle = 2500
        self.ca.set_pv_value(FREQUENCY, freq)
        self.ca.set_pv_value("MNTCYCLES:SP", maintenance_cycles_before_rotation)
        self.ca.set_pv_value("CYCLE", current_cycle)

        inverted_freq = 1/freq

        seconds_to_rotation = (inverted_freq * maintenance_cycles_before_rotation) - (inverted_freq * current_cycle)

        self.ca.assert_that_pv_is("MNTTIME", seconds_to_rotation)
