import unittest
import time
from common_tests.oscillating_collimators import (
    OscillatingCollimatorBase,
    _custom_name_func,
    RADIUS,
    ANGLE,
    FREQUENCY,
    DISCRIMINANT,
    GALIL_ADDR,
    OSC_PREFIX,
    MOT_PREFIX,
)
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from parameterized import parameterized
import os
from utils.test_modes import TestModes


# The default motor resoltuion is chosen because this is reolution used when extracting the original numbers from LabView
DEFAULT_MOTOR_RESOLUTION = 0.00250
test_path = os.path.realpath(
    os.path.join(
        os.getenv("EPICS_KIT_ROOT"),
        "support",
        "motorExtensions",
        "master",
        "settings",
        "oscillatingCollimator",
    )
)
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
    Tests for the LET Oscillating collimator.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        ca_mot = ChannelAccess()
        ca_mot.assert_that_pv_exists("MOT:MTR0103", timeout=30)
        ca_mot.assert_setting_setpoint_sets_readback(
            DEFAULT_MOTOR_RESOLUTION,
            set_point_pv="MOT:MTR0103.MRES",
            readback_pv="MOT:MTR0103.MRES",
        )
        self.ca = ChannelAccess(device_prefix=OSC_PREFIX, default_wait_time=0)
        self.ca_mot = ChannelAccess(device_prefix=MOT_PREFIX, default_wait_time=0)
        self.ca.assert_that_pv_exists("VEL:SP", timeout=30)

        # Set to 0 so stability buffer contents are consistent & known for each test
        # Takes 10 seconds for buffer to have consistent contents, so to be certain sleep for 11
        self.ca_mot.set_pv_value("DMC01:Galil0Bi5_STATUS", 0, sleep_after_set=11)

    @parameterized.expand(
        # [(angle, frequency, radius), (expected distance, expected velocity)
        # Values confirmed via LabView VI
        [
            [(2.0, 0.5, 10.0), (281, 283)],
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
            [(0.5, 0.1, 50.0), (349, 70)],
        ],
        testcase_func_name=_custom_name_func,
    )
    def test_GIVEN_angle_frequency_and_radius_WHEN_set_THEN_distance_and_velocity_match_LabView_generated_values(
        self, settings, expected_values
    ):
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

    def test_WHEN_input_values_cause_discriminant_to_be_negative_THEN_discriminant_pv_is_one(self):
        # Act
        # in normal operations the radius is not dynamic so set it first so it is considered in future calcs
        self.ca.set_pv_value(RADIUS, 1000.0)
        self.ca.set_pv_value(ANGLE, 2.0)
        self.ca.set_pv_value(FREQUENCY, 0.5)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 1.0)

    def test_WHEN_laser_unstable_THEN_collimator_is_reported_moving(self):
        # Act
        # Check that PV was stopped, then starts moving after laser change
        self.ca.assert_that_pv_is("MOVING", "Not Moving", timeout=30)
        self.ca.assert_that_pv_value_is_unchanged("MOVING", 5)
        # Give laser new value
        self.ca_mot.set_pv_value("DMC01:Galil0Bi5_STATUS", 1)

        # Assert
        # Check PV is now moving
        # Buffer contents stay consistent for 10 seconds; check for 5 to avoid race conditions
        self.ca.assert_that_pv_is("MOVING", "Moving", timeout=30)
        self.ca.assert_that_pv_value_is_unchanged("MOVING", 5)

    def test_WHEN_laser_stable_THEN_collimator_is_reported_not_moving(self):
        # Act
        self.ca_mot.set_pv_value("DMC01:Galil0Bi5_STATUS", 1)

        # Assert
        # Check that PV was moving after laser change, then stops moving after buffer clears
        # Takes 10 seconds for buffer to have consistent contents; check for 5 to avoid race conditions
        self.ca.assert_that_pv_is("MOVING", "Moving", timeout=30)
        self.ca.assert_that_pv_value_is_unchanged("MOVING", 5)
        time.sleep(5)
        # Check PV is now stopped (and stays stopped)
        self.ca.assert_that_pv_is("MOVING", "Not Moving", timeout=30)
        self.ca.assert_that_pv_value_is_unchanged("MOVING", 5)
