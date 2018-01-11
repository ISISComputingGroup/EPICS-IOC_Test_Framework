import unittest
import math
import time
from itertools import starmap

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir

# Internal Address of device (must be 2 characters)
GALIL_ADDR = "128.0.0.0"

PREFIX = "MOT"

# These are the coordinates for the stored position of the beamstop are for the test configuration. These coordinates
# are the position in the X-Y plane that the arm will be at when it is pointing vertically upwards and at zero on the
# W axis.
STORE_X, STORE_Y = -6.8, 2.7

# Stored positions of theta / w motors. These are the expected position of the two "real" motors
THETA_STORED_POS = math.pi/2.-0.2  # Bit less than 90 degrees to avoid going out of range
THETA_ACTIVE_POS = math.pi/4.      # Active position has the arm at 45 degrees.
W_STORED_POS = -2.0                # Bit less than 0 for the horizontal motor position
W_ACTIVE_POS = 0.                  # Active position has the arm at the position the motor started at

# These are the coordinates for the active position of the beamstop are for the test configuration. These coordinates
# are the position in the X-Y plane that the arm will be at when it is pointing diagonally at 45 degrees and at zero
# in the W axis.
ACTIVE_X, ACTIVE_Y = 0., 0.

# Flags for whether the arm should be active or stored
ACTIVE, STORE = 0, 1

# Motor position tolerance
TOLERANCE = 2e-1
# Length of time to wait for RBV to reach setpoint
RBV_TIMEOUT = 50

# PV names for X/Y motors
MOTOR_X = "MOT:ARM:X"
MOTOR_Y = "MOT:ARM:Y"
MOTOR_X_RBV = "MOT:ARM:X.RBV"
MOTOR_Y_RBV = "MOT:ARM:Y.RBV"

# PV names for "real" motors
MTR1 = "MOT:MTR0101"
MTR2 = "MOT:MTR0102"

# PV for store/active command
STORE_PV = "MOT:ARM:STORE"
STORE_SP = "ARM:STORE:SP"

# PV for tweaking X/Y position
TWEAK_X = "ARM:X:TWEAK"
TWEAK_Y = "ARM:Y:TWEAK"


IOCS = [
    {
        "name": "GALIL_01",
        "directory": get_default_ioc_dir("GALIL"),
        "macros": {
            "GALILADDR01": GALIL_ADDR,
            "IFXYBEAMSTOP": " ",
        },
    },
]


class XyarmbeamstopTests(unittest.TestCase):
    """
    Tests for the Larmor X-Y Beamstop
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.wait_for(MOTOR_X, timeout=60)
        self._set_pv_value(STORE_SP, ACTIVE)
        self._assert_setpoint_and_readback_reached(ACTIVE_X, ACTIVE_Y)

    def _set_pv_value(self, pv_name, value):
        self.ca.set_pv_value("{0}:{1}".format(PREFIX, pv_name), value)

    def _set_x(self, value):
        self._set_pv_value("ARM:X:SP", value)

    def _set_y(self, value):
        self._set_pv_value("ARM:Y:SP", value)

    def _assert_setpoint_and_readback_reached(self, x_position, y_position):
        """
        Check that both the setpoint for has been set and the readback value reaches that setpoint
        :param x_position: the expected value to move the x axis to
        :param y_position: the expected value to move the y axis to
        :return:
        """
        self.ca.assert_that_pv_is_number(MOTOR_X, x_position, TOLERANCE)
        self.ca.assert_that_pv_is_number(MOTOR_Y, y_position, TOLERANCE)
        self.ca.assert_that_pv_is_number(MOTOR_X_RBV, x_position, TOLERANCE, timeout=RBV_TIMEOUT)
        self.ca.assert_that_pv_is_number(MOTOR_Y_RBV, y_position, TOLERANCE, timeout=RBV_TIMEOUT)

    def test_WHEN_set_x_y_THEN_beamstop_moves_to_set_position(self):
        x = 1.0
        y = 2.0
        self._set_x(x)
        self._set_y(y)

        self._assert_setpoint_and_readback_reached(x, y)

    def test_WHEN_set_to_store_state_THEN_beamstop_move_to_store_position(self):
        self._set_pv_value(STORE_SP, STORE)

        self._assert_setpoint_and_readback_reached(STORE_X, STORE_Y)

        self.ca.assert_that_pv_is(STORE_PV, "STORED")

        self._assert_setpoint_and_readback_reached(STORE_X, STORE_Y)

        self.ca.assert_that_pv_is_number(MTR1, THETA_STORED_POS, TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR2, W_STORED_POS, TOLERANCE)

    def test_GIVEN_beamstop_in_stored_state_WHEN_try_to_move_beamstop_THEN_beamstop_cannot_be_move(self):
        # store the arm
        self._set_pv_value(STORE_SP, STORE)

        self._assert_setpoint_and_readback_reached(STORE_X, STORE_Y)

        # Now try and move it. This should not move as the motor has put access disabled.
        attempted_move_x = 0.2
        attempted_move_y = 0.2
        self._set_x(attempted_move_x)
        self._set_y(attempted_move_y)

        self.ca.assert_that_pv_is(STORE_PV, "STORED")
        self._assert_setpoint_and_readback_reached(STORE_X, STORE_Y)

        self.ca.assert_that_pv_is_number(MTR1, THETA_STORED_POS, TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR2, W_STORED_POS, TOLERANCE)

    def test_GIVEN_beamstop_in_stored_state_WHEN_set_to_active_state_THEN_beamstop_moves_to_active_position(self):
        # First put it into stored mode
        self._set_pv_value(STORE_SP, STORE)

        self._assert_setpoint_and_readback_reached(STORE_X, STORE_Y)

        # Then check it comes back out
        self._set_pv_value(STORE_SP, ACTIVE)

        self.ca.assert_that_pv_is(STORE_PV, "ACTIVE")

        self._assert_setpoint_and_readback_reached(ACTIVE_X, ACTIVE_Y)

        self.ca.assert_that_pv_is_number(MTR1, THETA_ACTIVE_POS, TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR2, W_ACTIVE_POS, TOLERANCE)

    def test_WHEN_tweak_x_in_positive_direction_THEN_x_is_offset_relative_to_current_position_by_given_amount(self):
        start_x = 1.0
        tweak_x = 0.1
        expected_x = 1.1

        self._set_x(start_x)
        self._set_pv_value(TWEAK_X, tweak_x)

        self.ca.assert_that_pv_is_number(MOTOR_X, expected_x, TOLERANCE)
        self.ca.assert_that_pv_is_number(MOTOR_X_RBV, expected_x, TOLERANCE)

    def test_WHEN_tweak_y_in_positive_direction_THEN_y_is_offset_relative_to_current_position_by_given_amount(self):
        start_y = 1.0
        tweak_y = 0.1
        expected_y = 1.1

        self._set_y(start_y)
        self._set_pv_value(TWEAK_Y, tweak_y)

        self.ca.assert_that_pv_is_number(MOTOR_Y, expected_y, TOLERANCE)
        self.ca.assert_that_pv_is_number(MOTOR_Y_RBV, expected_y, TOLERANCE)

    def test_WHEN_tweak_x_in_negative_direction_THEN_x_is_offset_relative_to_current_position_by_given_amount(self):
        start_x = 1.0
        tweak_x = -0.1
        expected_x = 0.9

        self._set_x(start_x)
        self._set_pv_value(TWEAK_X, tweak_x)

        self.ca.assert_that_pv_is_number(MOTOR_X, expected_x, TOLERANCE)
        self.ca.assert_that_pv_is_number(MOTOR_X_RBV, expected_x, TOLERANCE)

    def test_WHEN_tweak_y_in_negative_direction_THEN_y_is_offset_relative_to_current_position_by_given_amount(self):
        start_y = 1.0
        tweak_y = -0.1
        expected_y = 0.9

        self._set_y(start_y)
        self._set_pv_value(TWEAK_Y, tweak_y)

        self.ca.assert_that_pv_is_number(MOTOR_Y, expected_y, TOLERANCE)
        self.ca.assert_that_pv_is_number(MOTOR_Y_RBV, expected_y, TOLERANCE)

    def test_WHEN_set_shutter_to_open_THEN_shutter_is_set_to_open_state(self):
        self._set_pv_value("SHUTTERS:SP", 1)
        self.ca.assert_that_pv_is("MOT:SHUTTERS", "OPEN")
