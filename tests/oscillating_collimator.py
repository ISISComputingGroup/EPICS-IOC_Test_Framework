import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister

# IP address of device
GALIL_ADDR = "128.0.0.0"

# MACROS to use for the IOC
MACROS = {
    "GALILADDR": GALIL_ADDR,
    "MTRCTRL": "01"
    "IFOSCCOL": " "
}
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
    Tests for the LET Oscillating collimator.

    The CA.Client.Exceptions these tests generate are expected because of a workaround we had to make in the DB
    file to prevent a hang in the case of using asynFloat64 for the SP types. Issue described in ticket #2736
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("oscillating_collimator")
        ChannelAccess().wait_for("MOT:MTR0101", timeout=30)
        self.ca = ChannelAccess(device_prefix=PREFIX)
        self.ca.wait_for("VEL:SP", timeout=30)

    def test_GIVEN_angle_frequency_and_radius_WHEN_set_THEN_distance_and_velocity_match_LabView_generated_values(self):

        # Arrange
        # Dictionary outputs[(angle, frequency, radius)] = (distance, velocity)
        # Values confirmed via LabView VI
        outputs = dict()

        outputs[(2.0, 0.5, 10.0)] = (281, 283)
        outputs[(1.0, 0.5, 10.0)] = (140, 140)
        outputs[(0.5, 0.5, 10.0)] = (70, 70)

        outputs[(2.0, 0.1, 10.0)] = (279, 56)
        outputs[(1.0, 0.1, 10.0)] = (140, 28)
        outputs[(0.5, 0.1, 10.0)] = (70, 14)

        outputs[(2.0, 0.5, 50.0)] = (1442, 1487)
        outputs[(1.0, 0.5, 50.0)] = (709, 719)
        outputs[(0.5, 0.5, 50.0)] = (352, 354)

        outputs[(2.0, 0.1, 50.0)] = (1398, 280)
        outputs[(1.0, 0.1, 50.0)] = (699, 140)
        outputs[(0.5, 0.1, 50.0)] = (349, 70)

        tolerance = 0.5

        for key in outputs.keys():
            # Act
            self.ca.set_pv_value(ANGLE, key[0])
            self.ca.set_pv_value(FREQUENCY, key[1])
            self.ca.set_pv_value(RADIUS, key[2])

            # Assert
            self.ca.assert_that_pv_is_number("DIST:SP", outputs[key][0], tolerance)
            self.ca.assert_that_pv_is_number("VEL:SP", outputs[key][1], tolerance)

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

    def test_WHEN_mounting_radius_set_negative_THEN_mounting_radius_is_zero(self):
        self.ca.set_pv_value(RADIUS, -1.0)
        self.ca.assert_that_pv_is_number(RADIUS, 0.0)

    def test_WHEN_input_values_cause_discriminant_to_be_negative_THEN_discriminant_pv_is_one(self):

        # Act
        self.ca.set_pv_value(ANGLE, 2.0)
        self.ca.set_pv_value(FREQUENCY, 0.5)
        self.ca.set_pv_value(RADIUS, 1000.0)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 1.0)

    def test_WHEN_input_values_cause_discriminant_to_be_positive_THEN_discriminant_pv_is_zero(self):

        # Act
        self.ca.set_pv_value(ANGLE, 2.0)
        self.ca.set_pv_value(FREQUENCY, 0.5)
        self.ca.set_pv_value(RADIUS, 1.0)

        # Assert
        self.ca.assert_that_pv_is_number(DISCRIMINANT, 0.0)

    def test_WHEN_collimator_running_THEN_thread_is_not_on_reserved_thread(self):
        # Threads 0 and 1 are reserved for homing under IBEX
        self.ca.assert_that_pv_is_not("THREAD", "0")
        self.ca.assert_that_pv_is_not("THREAD", "1")
