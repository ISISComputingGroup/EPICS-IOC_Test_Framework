import unittest
import math
import time
from itertools import starmap

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister

# Internal Address of device (must be 2 characters)
GALIL_ADDR = "128.0.0.0"

# MACROS to use for the IOC
MACROS = {"GALILADDR01": GALIL_ADDR}
PREFIX = "MOT:OSCCOL"

# Commonly used PVs
ANGLE = "ANGLE:SP"
FREQUENCY = "FREQ:SP"
RADIUS = "RADIUS:SP"
VELOCITY = "VEL:SP"
DISTANCE = "DIST:SP"
DISCRIMINANT = "VEL:SP:DISC:CHECK"

class Oscillating_collimatorTests(unittest.TestCase):
    """
    Tests for the Larmor X-Y Beamstop
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("oscillating_collimator")
        self.ca = ChannelAccess(device_prefix=PREFIX)
        self.ca.wait_for("VEL:SP", timeout=30)

    def test_GIVEN_angle_frequency_and_radius_WHEN_set_THEN_distance_and_velocity_match_LV_generated_values(self):

        # Arrange
        # Dictionary outputs[(angle, frequency, radius)] = (distance, velocity)
        # Values confirmed via LabView VI
        outputs = dict()

        outputs[(2, 0.5, 10)] = (281, 283)
        outputs[(1, 0.5, 10)] = (140, 140)
        outputs[(0.5, 0.5, 10)] = (70, 70)

        outputs[(2, 0.1, 10)] = (279, 56)
        outputs[(1, 0.1, 10)] = (140, 28)
        outputs[(0.5, 0.1, 10)] = (70, 14)

        outputs[(2, 0.5, 50)] = (1442, 1487)
        outputs[(1, 0.5, 50)] = (709, 719)
        outputs[(0.5, 0.5, 50)] = (352, 354)

        outputs[(2, 0.1, 50)] = (1398, 280)
        outputs[(1, 0.1, 50)] = (699, 140)
        outputs[(0.5, 0.1, 50)] = (349, 70)

        tolerance = 2

        for key in outputs.keys():
            # Act
            self.ca.set_pv_value(ANGLE, key[0])
            self.ca.set_pv_value(FREQUENCY, key[1])
            self.ca.set_pv_value(RADIUS, key[2])

            # Assert
            self.ca.assert_that_pv_is_number("DIST:SP", outputs[key][0], tolerance)
            self.ca.assert_that_pv_is_number("VEL:SP", outputs[key][1], tolerance)

    def test_WHEN_angle_set_negative_THEN_angle_is_zero(self):
        self.ca.set_pv_value(ANGLE, -1)
        self.ca.assert_that_pv_is_number(ANGLE, 0)

    def test_WHEN_angle_set_greater_than_two_THEN_angle_is_two(self):
        self.ca.set_pv_value(ANGLE, 5)
        self.ca.assert_that_pv_is_number(ANGLE, 2)

    def test_WHEN_frequency_set_negative_THEN_angle_is_zero(self):
        self.ca.set_pv_value(FREQUENCY, -1)
        self.ca.assert_that_pv_is_number(FREQUENCY, 0)

    def test_WHEN_angle_set_greater_than_half_THEN_angle_is_half(self):
        self.ca.set_pv_value(FREQUENCY, 1)
        self.ca.assert_that_pv_is_number(FREQUENCY, 0.5)

    def test_WHEN_frq_set_greater_than_two_THEN_angle_is_two(self):
        self.ca.set_pv_value(ANGLE, 5)
        self.ca.assert_that_pv_is_number(ANGLE, 2)

    def test_WHEN_mounting_radius_set_negative_THEN_mounting_radius_is_zero(self):
        self.ca.set_pv_value(RADIUS, -1)
        self.ca.assert_that_pv_is_number(RADIUS, 0)

    def test_WHEN_input_values_cause_discriminant_to_be_negative_THEN_discriminant_pv_is_one(self):

        # Act
        self.ca.set_pv_value(ANGLE, 2)
        self.ca.set_pv_value(FREQUENCY, 0.5)
        self.ca.set_pv_value(RADIUS, 1000)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 1)

    def test_WHEN_input_values_cause_discriminant_to_be_positive_THEN_discriminant_pv_is_zero(self):

        # Act
        self.ca.set_pv_value(ANGLE, 2)
        self.ca.set_pv_value(FREQUENCY, 0.5)
        self.ca.set_pv_value(RADIUS, 1)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 0)

    # Generating a zero discriminant is practically impossible owing to floating point rounding and trigonometric functions
    def test_WHEN_input_values_cause_discriminant_to_be_zero_THEN_discriminant_pv_is_zero(self):
        pass

    def test_WHEN_collimator_running_THEN_thread_is_set_to_two(self):
        self.ca.assert_that_pv_is("THREAD", "2")
