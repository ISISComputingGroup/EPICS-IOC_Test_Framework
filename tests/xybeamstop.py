import unittest
import math
import time

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister

# Internal Address of device (must be 2 characters)
GALIL_ADDR = "128.0.0.0"

# MACROS to use for the IOC
MACROS = {"GALILADDR01": GALIL_ADDR}

PREFIX = "MOT"
MTR1 = "MOT:MTR0101"
MTR2 = "MOT:MTR0102"

# These are the coordinates for the stored position of the beamstop are for the test configuration. These coordinates
# are the position in the X-Y plane that the arm will be at when it is pointing vertically upwards and at zero on the
# W axis.
STORE_X, STORE_Y = -7.071, 2.929

# These are the coordinates for the active position of the beamstop are for the test configuration. These coordinates
# are the position in the X-Y plane that the arm will be at when it is pointing diagonally at 45 degrees and at zero
# in the W axis.
ACTIVE_X, ACTIVE_Y = 0., 0.

# Flags for whether the arm should be active or stored
ACTIVE, STORE = 0, 1

# Motor position tolerance
TOLERANCE = 1e-2


class XybeamstopTests(unittest.TestCase):
    """
    Tests for the Larmor X-Y Beamstop
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("xyBeamstop")
        self.ca = ChannelAccess()
        self.ca.wait_for("MOT:ARM:X", timeout=30)
        self._set_pv_value("ARM:STORE", ACTIVE)
        self._set_x(0.1)
        self._set_y(0.1)

    def _set_pv_value(self, pv_name, value):
        self.ca.set_pv_value("{0}:{1}".format(PREFIX, pv_name), value)

    def _set_x(self, value):
        self._set_pv_value("ARM:X", value)

    def _set_y(self, value):
        self._set_pv_value("ARM:Y", value)

    def test_WHEN_set_x_y_THEN_beamstop_moves_to_set_position(self):
        x = 1.0
        y = 2.0
        self._set_x(x)
        self._set_y(y)

        self.ca.assert_that_pv_is_number("MOT:ARM:X", x, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y", y, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:X.RBV", x, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y.RBV", y, TOLERANCE)

    def test_WHEN_set_to_store_state_THEN_beamstop_move_to_store_position(self):
        self._set_pv_value("ARM:STORE", STORE)

        self.ca.assert_that_pv_is("MOT:ARM:STORE", "STORED")
        self.ca.assert_that_pv_is_number("MOT:ARM:X", STORE_X, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y", STORE_Y, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:X.RBV", STORE_X, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y.RBV", STORE_Y, TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR1, math.pi/2., TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR2, 0, TOLERANCE)

    def test_GIVEN_beamstop_in_stored_state_WHEN_try_to_move_beamstop_THEN_beamstop_cannot_be_move(self):
        # store the arm
        self._set_pv_value("ARM:STORE:SP", STORE)

        # Now try and move it. This should not move as the motor has put access disabled.
        self._set_x(0.2)
        self._set_y(0.2)

        self.ca.assert_that_pv_is("MOT:ARM:STORE", "STORED")
        self.ca.assert_that_pv_is_number("MOT:ARM:X", STORE_X, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y", STORE_Y, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:X.RBV", STORE_X, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y.RBV", STORE_Y, TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR1, math.pi/2., TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR2, 0, TOLERANCE)

    def test_GIVEN_beamstop_in_stored_state_WHEN_set_to_active_state_THEN_beamstop_moves_to_active_position(self):
        self._set_pv_value("ARM:STORE", STORE)  # First put it into stored mode
        self._set_pv_value("ARM:STORE", ACTIVE)  # Then check it comes back out

        self.ca.assert_that_pv_is("MOT:ARM:STORE", "ACTIVE")
        self.ca.assert_that_pv_is("MOT:ARM:X", ACTIVE_X)
        self.ca.assert_that_pv_is("MOT:ARM:Y", ACTIVE_Y)
        self.ca.assert_that_pv_is_number("MOT:ARM:X.RBV", ACTIVE_X, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y.RBV", ACTIVE_Y, TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR1, math.pi/4., TOLERANCE)
        self.ca.assert_that_pv_is_number(MTR2, 0, TOLERANCE)

    def test_WHEN_tweak_x_in_positive_direction_THEN_x_is_offset_relative_to_current_position_by_given_amount(self):
        self._set_x(1.0)
        self._set_pv_value("ARM:X:TWEAK", 0.1)

        self.ca.assert_that_pv_is_number("MOT:ARM:X", 1.1, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:X.RBV", 1.1, TOLERANCE)

    def test_WHEN_tweak_y_in_positive_direction_THEN_y_is_offset_relative_to_current_position_by_given_amount(self):
        self._set_y(1.0)
        self._set_pv_value("ARM:Y:TWEAK", 0.1)

        self.ca.assert_that_pv_is_number("MOT:ARM:Y", 1.1, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y.RBV", 1.1, TOLERANCE)

    def test_WHEN_tweak_x_in_negative_direction_THEN_x_is_offset_relative_to_current_position_by_given_amount(self):
        self._set_x(1.0)
        self._set_pv_value("ARM:X:TWEAK", -0.1)

        self.ca.assert_that_pv_is_number("MOT:ARM:X", 0.9, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:X.RBV", 0.9, TOLERANCE)

    def test_WHEN_tweak_y_in_negative_direction_THEN_y_is_offset_relative_to_current_position_by_given_amount(self):
        self._set_y(1.0)
        self._set_pv_value("ARM:Y:TWEAK", -0.1)

        self.ca.assert_that_pv_is_number("MOT:ARM:Y", 0.9, TOLERANCE)
        self.ca.assert_that_pv_is_number("MOT:ARM:Y.RBV", 0.9, TOLERANCE)

    def test_WHEN_set_shutter_to_open_THEN_shutter_is_set_to_open_state(self):
        self._set_pv_value("SHUTTERS:SP", 1)

        self.ca.assert_that_pv_is("MOT:SHUTTERS", "OPEN")
