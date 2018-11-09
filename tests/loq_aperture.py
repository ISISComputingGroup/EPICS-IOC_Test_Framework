import unittest
import os
import math
from unittest import skip

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from parameterized import parameterized

# Internal Address of device (must be 2 characters)
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"

PREFIX = "MOT"

## Motor position tolerance
TOLERANCE = 2e-1
## Length of time to wait for RBV to reach setpoint
#RBV_TIMEOUT = 50
#
## PV names for X/Y motors
MOTOR = "MOT:MTR0101"
#MOTOR_Y = "MOT:ARM:Y"
#MOTOR_X_RBV = "MOT:ARM:X.RBV"
#MOTOR_Y_RBV = "MOT:ARM:Y.RBV"
#
## PV names for "real" motors
#MTR1 = "MOT:MTR0101"
#MTR2 = "MOT:MTR0102"
#
## PV for store/active command
#STORE_PV = "MOT:ARM:STORE"
#STORE_SP = "ARM:STORE:SP"
#
## PV for tweaking X/Y position
#TWEAK_X = "ARM:X:TWEAK"
#TWEAK_Y = "ARM:Y:TWEAK"

## Axis position index PV and SP
POSITION_INDEX = "LKUP:APERTURE:IPOSN"
POSITION_SP = "LKUP:APERTURE:IPOSN:SP"

## PV reading closest beamstop position
CLOSESTSHUTTER = "APERTURE:CLOSESTSHUTTER"

## PV which sends the motor to closest beamstop motion set point
CLOSEAPERTURE = "APERTURE:CLOSEAPERTURE"

test_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, "test_support", "loq_aperture"))

IOCS = [
    {
        "name": "GALIL_01",
        "directory": get_default_ioc_dir("GALIL"),
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "IFLOQAPERTURE": " ",
            "MTRCTRL": "1",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
            "ICPCONFIGROOT": test_path.replace("\\", "/"),
        },
    },
]


TEST_MODES = [TestModes.DEVSIM]

#@skip("This test is very unstable. It should work; it has been disabled so that we can see other failures on Jenkins")
class LoqApertureTests(unittest.TestCase):
    """
    Tests for the LOQ Aperture
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.assert_that_pv_exists(MOTOR, timeout=60)
        self.ca.assert_that_pv_exists(CLOSESTSHUTTER)
        self.ca.assert_that_pv_exists(CLOSEAPERTURE)


    # BX refers to a blanking plate; AX refers to an aperture hole. Closest positions defined in ticket 3623
    @parameterized.expand([
        ("start_B1", 0, 0),
        ("start_A1", 1, 2),
        ("start_B2", 2, 2),
        ("start_A2", 3, 4),
        ("start_B3", 4, 4),
        ("start_A3", 5, 4),
        ("start_B4", 6, 6),
    ])
    def test_GIVEN_motor_on_an_aperture_position_WHEN_motor_set_to_closest_beamstop_THEN_motor_moves_to_closest_beamstop(self, _, start_pos, closest_stop):
        # GIVEN
        self.ca.set_pv_value(POSITION_SP, start_pos)
        self.ca.assert_that_pv_is_number(POSITION_INDEX, start_pos, tolerance=TOLERANCE)

        # WHEN
        self.ca.process_pv(CLOSEAPERTURE)

        # THEN
        self.ca.assert_that_pv_is_number(CLOSESTSHUTTER, closest_stop)
        self.ca.assert_that_pv_is_number(POSITION_INDEX, closest_stop, timeout=5)

#    @parameterized.expand([
#        ("start_B1", 0, 0),
#        ("start_A1", 1, 2),
#        ("start_B2", 2, 2),
#        ("start_A2", 3, 4),
#        ("start_B3", 4, 4),
#        ("start_A3", 5, 4),
#        ("start_B4", 6, 6),
#    ])
#    def test_GIVEN_motor_between_setpoint_positions_WHEN_motor_set_to_closest_beamstop_THEN_motor_moves_to_closest_beamstop(self, start_pos, closest_stop):
#        # GIVEN
#        self.ca.set_pv_value(MOTOR, start_pos)
#        self.ca.assert_that_pv_is_number(MOTOR, start_pos, TOLERANCE)
#        self.ca.assert_that_pv_is_number(MOTOR, start_pos, tolerance=TOLERANCE)
#
#        # WHEN
#        self.ca.process_pv(CLOSEAPERTURE)
#
#        # THEN
#        self.ca.assert_that_pv_is_number(CLOSESTSHUTTER, closest_stop)
#        self.ca.assert_that_pv_is_number(MOTOR, closest_stop, timeout=60)


#    def _set_pv_value(self, pv_name, value):
#        self.ca.set_pv_value("{0}:{1}".format(PREFIX, pv_name), value)
#
#    def _set_x(self, value):
#        self._set_pv_value("ARM:X:SP", value)
#
#    def _set_y(self, value):
#        self._set_pv_value("ARM:Y:SP", value)
#
#    def _assert_setpoint_and_readback_reached(self, x_position, y_position):
#        """
#        Check that both the setpoint for has been set and the readback value reaches that setpoint
#        :param x_position: the expected value to move the x axis to
#        :param y_position: the expected value to move the y axis to
#        :return:
#        """
#        self.ca.assert_that_pv_is_number(MOTOR_X, x_position, TOLERANCE)
#        self.ca.assert_that_pv_is_number(MOTOR_Y, y_position, TOLERANCE)
#        self.ca.assert_that_pv_is_number(MOTOR_X_RBV, x_position, TOLERANCE, timeout=RBV_TIMEOUT)
#        self.ca.assert_that_pv_is_number(MOTOR_Y_RBV, y_position, TOLERANCE, timeout=RBV_TIMEOUT)

