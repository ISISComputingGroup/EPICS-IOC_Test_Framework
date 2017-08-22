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


class XybeamstopTests(unittest.TestCase):
    """
    Tests for the Larmor X-Y Beamstop
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("xyBeamstop")
        self.ca = ChannelAccess()
        self.ca.wait_for("MOT:ARM:X")
        self._set_pv_value("ARM:STORE", 0)
        self._set_x(0.1)
        self._set_y(0.1)

    def _set_pv_value(self, pv_name, value):
        self.ca.set_pv_value("{0}:{1}".format(PREFIX, pv_name), value)

    def _set_x(self, value):
        self._set_pv_value("ARM:X", value)

    def _set_y(self, value):
        self._set_pv_value("ARM:Y", value)

    def test_GIVEN_x_y_WHEN_read_x_y_THEN_x_y_is_as_expected(self):
        x = 1.0
        y = 2.0
        self._set_x(x)
        time.sleep(2)
        self._set_y(y)
        time.sleep(4)

        self.ca.assert_that_pv_is_close("MOT:ARM:X", x, 1e-2)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y", y, 1e-2)
        self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", x, 1e-1)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", y, 1e-1)

    def test_GIVEN_store_command_WHEN_read_x_y_is_as_expected(self):
        self._set_pv_value("ARM:STORE", 1)
        time.sleep(1)

        self.ca.assert_that_pv_is("MOT:ARM:STORE", "STORED")
        self.ca.assert_that_pv_is_close("MOT:ARM:X", -7.071)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y", 2.929)
        self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", -7.071, 1e-2)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", 2.929, 1e-2)
        self.ca.assert_that_pv_is_close(MTR1, math.pi/2.)
        self.ca.assert_that_pv_is_close(MTR2, 0)

    def test_GIVEN_store_command_THEN_cannot_move_arm(self):
        # store the arm
        self._set_pv_value("ARM:STORE:SP", 1)

        # Now try and move it. This should not move as the motor has put access disabled.
        self._set_x(0.2)
        self._set_y(0.2)

        time.sleep(1)

        self.ca.assert_that_pv_is("MOT:ARM:STORE", "STORED")
        self.ca.assert_that_pv_is_close("MOT:ARM:X", -7.071)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y", 2.929)
        self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", -7.071, 1e-2)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", 2.929, 1e-2)
        self.ca.assert_that_pv_is_close(MTR1, math.pi/2.)
        self.ca.assert_that_pv_is_close(MTR2, 0)

    def test_GIVEN_activate_command_sent_in_stored_mode_WHEN_read_x_y_is_as_expected(self):
        self._set_pv_value("ARM:STORE", 1)  # First put it into stored mode
        self._set_pv_value("ARM:STORE", 0)  # Then check it comes back out

        time.sleep(2)

        self.ca.assert_that_pv_is("MOT:ARM:STORE", "ACTIVE")
        self.ca.assert_that_pv_is("MOT:ARM:X", 0.)
        self.ca.assert_that_pv_is("MOT:ARM:Y", 0.)
        self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", 0, 0.6)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", 0, 0.6)
        self.ca.assert_that_pv_is_close(MTR1, math.pi/4., 1e-3)
        self.ca.assert_that_pv_is_close(MTR2, 0, 1e-3)
    #
    # def test_GIVEN_set_x_outside_lower_limit_WHEN_read_x_is_not_outside_limit(self):
    #     x_lower = -3.535
    #     self._set_x(x_lower)
    #     self._set_x(x_lower - 1.0)
    #     time.sleep(1)
    #     self.ca.assert_that_pv_is("MOT:ARM:X", x_lower)
    #     self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", x_lower, 1e-1)
    #
    # def test_GIVEN_set_x_outside_upper_limit_WHEN_read_x_is_not_outside_limit(self):
    #     x_upper = 3.535
    #     self._set_x(x_upper)
    #     self._set_x(x_upper + 1.0)
    #     time.sleep(1)
    #     self.ca.assert_that_pv_is("MOT:ARM:X", x_upper)
    #     self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", x_upper, 1e-1)
    #
    # def test_GIVEN_set_y_outside_lower_limit_WHEN_read_y_is_not_outside_limit(self):
    #     y_lower = -7.071
    #     self._set_y(y_lower)
    #     self._set_y(y_lower - 1.0)
    #     time.sleep(1)
    #     self.ca.assert_that_pv_is("MOT:ARM:Y", y_lower)
    #     self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", y_lower, 1e-1)
    #
    # def test_GIVEN_set_y_outside_upper_limit_WHEN_read_y_is_not_outside_limit(self):
    #     y_upper = 2.929
    #     self._set_y(y_upper)
    #     self._set_y(y_upper + 1.0)
    #     time.sleep(1)
    #     self.ca.assert_that_pv_is_close("MOT:ARM:Y", y_upper)
    #     self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", y_upper, 1e-2)

    def test_GIVEN_tweak_x_positive_WHEN_read_x_is_as_expected(self):
        self._set_x(1.0)
        self._set_pv_value("ARM:X:TWEAK", 0.1)
        time.sleep(1)

        self.ca.assert_that_pv_is_close("MOT:ARM:X", 1.1)
        self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", 1.1, 1e-2)

    def test_GIVEN_tweak_y_positive_WHEN_read_y_is_as_expected(self):
        self._set_y(1.0)
        self._set_pv_value("ARM:Y:TWEAK", 0.1)
        time.sleep(1)

        self.ca.assert_that_pv_is_close("MOT:ARM:Y", 1.1)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", 1.1, 1e-2)

    def test_GIVEN_tweak_x_negative_WHEN_read_x_is_as_expected(self):
        self._set_x(1.0)
        self._set_pv_value("ARM:X:TWEAK", -0.1)
        time.sleep(1)

        self.ca.assert_that_pv_is_close("MOT:ARM:X", 0.9)
        self.ca.assert_that_pv_is_close("MOT:ARM:X.RBV", 0.9, 1e-2)

    def test_GIVEN_tweak_y_negative_WHEN_read_y_is_as_expected(self):
        self._set_y(1.0)
        self._set_pv_value("ARM:Y:TWEAK", -0.1)
        time.sleep(1)

        self.ca.assert_that_pv_is_close("MOT:ARM:Y", 0.9)
        self.ca.assert_that_pv_is_close("MOT:ARM:Y.RBV", 0.9, 1e-2)

    def test_GIVEN_open_shutter_WHEN_read_shutter_is_open(self):
        self._set_pv_value("SHUTTERS:SP", 1)

        self.ca.assert_that_pv_is("MOT:SHUTTERS", "OPEN")
