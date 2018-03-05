import unittest
import math
import time
from itertools import starmap

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes


IOCS = [
    {
        "name": "LINMOT_01",
        "directory": get_default_ioc_dir("LINMOT"),
        "macros": {
            "AXIS1": "yes",
            "AXIS2": "yes",
            "AXIS3": "yes",
            "AXIS4": "yes",
            "MTRCTRL": "01",
            "IFGEMJAWS": " "
        },
    },
]


TEST_MODES = [TestModes.RECSIM]

# Motor position tolerance
TOLERANCE = 0.2

# PV names for calibrated motors
MOTOR_W = "MOT:JAWS6:CAL_W"
MOTOR_E = "MOT:JAWS6:CAL_E"
MOTOR_N = "MOT:JAWS6:CAL_N"
MOTOR_S = "MOT:JAWS6:CAL_S"


# PV names for "real" motors
UNDERLYING_MTR_WEST = "MOT:MTR0103"
UNDERLYING_MTR_EAST = "MOT:MTR0104"
UNDERLYING_MTR_NORTH = "MOT:MTR0101"
UNDERLYING_MTR_SOUTH = "MOT:MTR0102"

all_motors = [MOTOR_W, MOTOR_E, MOTOR_N, MOTOR_S,
              UNDERLYING_MTR_WEST, UNDERLYING_MTR_EAST, UNDERLYING_MTR_NORTH, UNDERLYING_MTR_SOUTH]

MIN_POSITION = 2
MID_POSITION = 5.4
MAX_POSITION = 12
TEST_POSITIONS = [MIN_POSITION, MID_POSITION, MAX_POSITION]

QUADRATIC_COEFFICIENTS = 0.03331, 0.07169, -0.13376
LINEAR_COEFFICIENTS = 1.025, 0

def calc_expected_quad_read(x):
    a, b, c = QUADRATIC_COEFFICIENTS
    return a * pow(x, 2) + b * x + c


def calc_expected_quad_write(y):
    a, b, c = QUADRATIC_COEFFICIENTS
    return (-b + pow(4 * a * (y - c) - pow(b, 2), 0.5)) / (2 * a)


def calc_expected_linear_read(x):
    b, c = LINEAR_COEFFICIENTS
    return b * x + c


def calc_expected_linear_write(y):
    b, c = LINEAR_COEFFICIENTS
    return (y - c) / b


class GemJawsTests(unittest.TestCase):
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

    def test_WHEN_underlying_quadratic_motor_set_to_a_position_THEN_calibrated_axis_as_expected(self):
        for motor in [MOTOR_W, MOTOR_E]:
            for position in TEST_POSITIONS:
                self._test_readback(motor, calc_expected_quad_read, position)

    def test_WHEN_calibrated_quadratic_motor_set_to_a_position_THEN_underlying_motor_as_expected(self):
        motors = {MOTOR_E: UNDERLYING_MTR_EAST, MOTOR_W: UNDERLYING_MTR_WEST}
        for mot, underlying in motors.items():
            for position in TEST_POSITIONS:
                self._test_set_point(underlying, mot, calc_expected_quad_write, position)

    def test_WHEN_underlying_linear_motor_set_to_a_position_THEN_calibrated_axis_as_expected(self):
        for motor in [MOTOR_N, MOTOR_S]:
            for position in TEST_POSITIONS:
                self._test_readback(motor, calc_expected_linear_read, position)

    def test_WHEN_calibrated_linear_motor_set_to_a_position_THEN_underlying_motor_as_expected(self):
        motors = {MOTOR_N: UNDERLYING_MTR_NORTH, MOTOR_S: UNDERLYING_MTR_SOUTH}
        for mot, underlying in motors.items():
            for position in TEST_POSITIONS:
                self._test_set_point(underlying, mot, calc_expected_linear_write, position)

    def test_WHEN_underlying_motor_stops_THEN_calibrated_motor_stops(self):
        # Move motor
        test_position = 7
        self.ca.set_pv_value(MOTOR_W, test_position)

        self.ca.set_pv_value(UNDERLYING_MTR_WEST + ".STOP", 1)
        self.ca.assert_that_pv_is(MOTOR_W + ".DMOV", 1)
        self.ca.assert_that_pv_is_not_number(MOTOR_W + ".RBV", test_position, TOLERANCE)
