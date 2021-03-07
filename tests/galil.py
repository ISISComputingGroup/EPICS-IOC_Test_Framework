import unittest
import time

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "GALIL_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL1": "01",
            "GALILADDR1": "127.0.0.1",
        },
    },
]

TEST_MODES = [TestModes.DEVSIM]


class GalilTests(unittest.TestCase):
    """
    Tests for galil motor controllers
    """
    controller = "01"
    num_motors = 8
    
    def zero_motors(self):
        for motor in ["{:02d}".format(mtr) for mtr in range(1, self.num_motors + 1)]:
            self.ca.set_pv_value("MOT:MTR{}{}".format(self.controller, motor), 0)
            self.ca.assert_that_pv_is("MOT:MTR{}{}".format(self.controller, motor), 0)
    
    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=None, default_timeout=20)

    def test_GIVEN_ioc_started_THEN_pvs_for_all_motors_exist(self):
        """
        check for real motors
        """
        for motor in ["{:02d}".format(mtr) for mtr in range(1, self.num_motors + 1)]:
            self.ca.assert_that_pv_exists("MOT:MTR{}{}".format(self.controller, motor))

    def test_GIVEN_ioc_started_THEN_axes_for_all_motors_exist(self):
        for motor in range(1, 8 + 1):
            self.ca.assert_that_pv_exists("GALIL_01:AXIS{}".format(motor))

    def test_GIVEN_motor_requested_to_move_THEN_motor_moves(self):
        self.zero_motors()

        # Move motor 0101
        val = 20.0
        self.ca.set_pv_value("MOT:MTR0101", val)
        self.ca.assert_that_pv_is("MOT:MTR0101", val)
        self.ca.assert_that_pv_is("MOT:MTR0101.RBV", val)

    def test_GIVEN_axis_requested_to_move_THEN_axis_moves(self):
        self.zero_motors()

        # Move axis 1
        val = 21.0
        self.ca.set_pv_value("GALIL_01:AXIS1:SP", val)
        self.ca.assert_that_pv_is("GALIL_01:AXIS1:SP:RBV", val)
        self.ca.assert_that_pv_is("GALIL_01:AXIS1", val)
        self.ca.assert_that_pv_is("MOT:MTR0101", val)
        self.ca.assert_that_pv_is("MOT:MTR0101.RBV", val)

    def test_GIVEN_motors_THEN_check_motor_encoder_diff_works(self):
        val = 10.0
        # setup motor using encoder
        self.ca.set_pv_value("MOT:MTR0101.UEIP", "Yes")
        self.ca.assert_that_pv_is("MOT:MTR0101.UEIP", "Yes")
        mres = self.ca.get_pv_value("MOT:MTR0101.MRES")
        eres = self.ca.get_pv_value("MOT:MTR0101.ERES")
        self.zero_motors()
        
        # move to initial position and check in step
        self.ca.set_pv_value("MOT:MTR0101", val)
        self.ca.assert_that_pv_is_number("MOT:MTR0101", val)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.RBV", val, tolerance=eres)
        self.ca.assert_that_pv_is_number("MOT:MTR0101_MTRENC_DIFF", 0.0, tolerance=eres)
        
        # now double encoder resolution so encoder now thinks it is at 2*val
        # giving difference (val - 2*val) 
        self.ca.set_pv_value("MOT:MTR0101.ERES", eres * 2.0)
        self.ca.assert_that_pv_is_number("MOT:MTR0101_MTRENC_DIFF", -val, tolerance=eres)
