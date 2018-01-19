import unittest
import math
import time
from itertools import starmap

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister

# MACROS to use for the IOC
MACROS = {
    "AXIS1": "yes",
    "AXIS2": "yes",
    "AXIS3": "yes",
    "AXIS4": "yes",
    "MTRCTRL": "01",
    "IFGEMJAWS": " "
}

# Motor position tolerance
TOLERANCE = 0.2

# PV names for calibrated motors
MOTOR_W = "MOT:JAWS6:CAL_W"

# PV names for "real" motors
UNDERLYING_MTR_WEST = "MOT:MTR0103"

all_motors = [MOTOR_W, UNDERLYING_MTR_WEST]


def calc_expected_quad_read(x):
    return 0.03331 * pow(x, 2) + 0.07169 * x - 0.13376


def calc_expected_quad_write(x):
    return (-0.07169 + pow(4 * 0.03331 * (x + 0.13376) - pow(0.07169, 2), 0.5)) / (2 * 0.03331)


class Gem_jawsTests(unittest.TestCase):
    """
    Tests for the gem beamscrapper jaws
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("gem_jaws")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.wait_for(MOTOR_W, timeout=60)
        [self.ca.set_pv_value(mtr + ".STOP", 1) for mtr in all_motors]

    def _test_readback(self, calibrated_axis, to_read_func, x):
        # Uses a sim record to save the time for the simulated motor to stop
        self.ca.set_pv_value(calibrated_axis + ":SIM:MTR:RBV", x)
        self.ca.assert_that_pv_is_number(calibrated_axis + ".RBV", to_read_func(x), TOLERANCE)

    def _test_set_point(self, underlying_motor, calibrated_axis, to_write_func, x):
        self.ca.set_pv_value(calibrated_axis, x)
        self.ca.assert_that_pv_is_number(underlying_motor + ".VAL", to_write_func(x), TOLERANCE)

    # Quadratic axis tests

    # Value used as it is near the low limit of the axis
    def test_WHEN_underlying_west_motor_set_to_2_THEN_calibrated_axis_as_expected(self):
        self._test_readback(MOTOR_W, calc_expected_quad_read, 2)

    def test_WHEN_underlying_west_motor_set_to_5_4_THEN_calibrated_axis_as_expected(self):
        self._test_readback(MOTOR_W, calc_expected_quad_read, 5.4)

    # Value used as it is near the high limit of the axis
    def test_WHEN_underlying_west_motor_set_to_12_THEN_calibrated_axis_as_expected(self):
        self._test_readback(MOTOR_W, calc_expected_quad_read, 12)

    # Value used as it is near the low limit of the axis
    def test_WHEN_calibrated_west_motor_set_to_2_THEN_underlying_motor_as_expected(self):
        self._test_set_point(UNDERLYING_MTR_WEST, MOTOR_W, calc_expected_quad_write, 2)

    def test_WHEN_calibrated_west_motor_set_to_5_4_THEN_underlying_motor_as_expected(self):
        self._test_set_point(UNDERLYING_MTR_WEST, MOTOR_W, calc_expected_quad_write, 5.4)

    # Value used as it is near the high limit of the axis
    def test_WHEN_calibrated_west_motor_set_to_12_THEN_underlying_motor_as_expected(self):
        self._test_set_point(UNDERLYING_MTR_WEST, MOTOR_W, calc_expected_quad_write, 12)

    def test_WHEN_underlying_motor_stops_THEN_calibrated_motor_stops(self):
        # Move motor
        test_position = 7
        self.ca.set_pv_value(MOTOR_W, test_position)

        self.ca.set_pv_value(UNDERLYING_MTR_WEST + ".STOP", 1)
        self.ca.assert_that_pv_is(MOTOR_W + ".DMOV", 1)
        self.ca.assert_that_pv_is_not_number(MOTOR_W + ".RBV", test_position, TOLERANCE)
