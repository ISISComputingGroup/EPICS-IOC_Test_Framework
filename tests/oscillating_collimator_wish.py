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

# Mechanically bound variables
MICROSTEPS_PER_STEP = 32 
GEARBOX_RATIO = 100 
ENC_COUNTS_PER_MM = 200
STEPS_PER_REV = 200
RADIUS = 375

IOCS = [
    {
        "name": "GALIL_01",
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
            "MICROSTEPS_PER_STEP": MICROSTEPS_PER_STEP, 
            "GEARBOX_RATIO": GEARBOX_RATIO,
            "ENC_COUNTS_PER_MM": ENC_COUNTS_PER_MM,
            "STEPS_PER_REV": STEPS_PER_REV,
            "RADIUS": RADIUS
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
        # [(angle, frequency, radius), (expected distance, expected velocity)
        # Values confirmed via LabView VI
        [[(1.125, 0.4, RADIUS), (2058.337, 1693.34)],
         [(2, 0.4, RADIUS), (3760.254, 3171.962)],
         [(1.1, 0.4, RADIUS), (2011.176, 1653.427)],
         [(1.233, 0.4, RADIUS), (2262.922, 1867.076)],
         ], testcase_func_name=_custom_name_func
    )
    def test_GIVEN_angle_frequency_and_radius_WHEN_set_THEN_distance_and_velocity_match_LabView_generated_values(self, settings, expected_values):

        # Arrange
        tolerance = 0.5

        # Act
        self.ca.set_pv_value(ANGLE, settings[0])
        self.ca.set_pv_value(FREQUENCY, settings[1])

        # Assert
        FULL_REV_STEPS = STEPS_PER_REV * MICROSTEPS_PER_STEP * GEARBOX_RATIO
        
        self.ca.assert_that_pv_is_number("FULLREV:SP", FULL_REV_STEPS, tolerance)
        # Allow for 0.1 degrees tolerance (steps per full rev/360 degrees/0.1)
        # This is to account for differences in precision of PI etc. between labview + epics
        self.ca.assert_that_pv_is_number("DIST:PART:SP", expected_values[0], tolerance=FULL_REV_STEPS/360/0.1)
        self.ca.assert_that_pv_is_number("VEL:SP", expected_values[1], tolerance)

    @parameterized.expand(
        [[0.4, 5000, 2500],
         [0.2, 10000, 800]]
    )
    def test_GIVEN_number_of_cycles_to_maintenance_rotation_THEN_time_to_maintenance_cycle_is_correct(self, freq, mnt_cycles, current_cycle):
        self.ca.set_pv_value(FREQUENCY, freq)
        self.ca.set_pv_value("MNTCYCLES", mnt_cycles)
        self.ca.set_pv_value("CYCLE", current_cycle)

        inverted_freq = 1/freq

        seconds_to_rotation = (inverted_freq * mnt_cycles) - (inverted_freq * current_cycle)

        self.ca.assert_that_pv_is("MNTTIME", seconds_to_rotation)
