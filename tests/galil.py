import unittest
import time
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import skip_if_nosim, skip_always

test_config_path = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "galil")
)

DEVICE_PREFIX = "GALIL_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "01",
            "GALILADDR1": "127.0.0.11",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
    },
]

DEFAULT_VELOCITY = 0.64

# parameters appropriate for galil hardware in R3 support office
MOTOR_SETUP = {
    "MOT:MTR{}{}_K1_SP": 0.000000,
    "MOT:MTR{}{}_K2_SP": 0.000000,
    "MOT:MTR{}{}_K3_SP": 0.000000,
    "MOT:MTR{}{}_ZP_SP": 0.000000,
    "MOT:MTR{}{}_ZN_SP": 0.000000,
    "MOT:MTR{}{}_TL_SP": 0.000000,
    "MOT:MTR{}{}_CP_SP": -1.000000,
    "MOT:MTR{}{}_CT_SP": 10.000000,
    "MOT:MTR{}{}_AF_SP": 0.000000,
    "MOT:MTR{}{}.PREM": "",
    "MOT:MTR{}{}.POST": "",
    "MOT:MTR{}{}.MRES": 0.0003125,
    "MOT:MTR{}{}.ERES": 0.0005,
    "MOT:MTR{}{}.VMAX": DEFAULT_VELOCITY,
    "MOT:MTR{}{}.VELO": DEFAULT_VELOCITY,
    "MOT:MTR{}{}.DESC": "Motor",
    "MOT:MTR{}{}.EGU": "mm",
    "MOT:MTR{}{}.ACCL": 1.000000,
    "MOT:MTR{}{}.BDST": 0.000000,
    "MOT:MTR{}{}.BVEL": DEFAULT_VELOCITY / 10.0,
    "MOT:MTR{}{}.BACC": 1.000000,
    "MOT:MTR{}{}.RDBD": 0.005000,
    "MOT:MTR{}{}.RTRY": 3,
    "MOT:MTR{}{}.RMOD": "Default",
    "MOT:MTR{}{}.HVEL": DEFAULT_VELOCITY,
    "MOT:MTR{}{}.PCOF": 0.000000e0,
    "MOT:MTR{}{}.ICOF": 0.000000e0,
    "MOT:MTR{}{}.DCOF": 0.000000e0,
    "MOT:MTR{}{}.UEIP": "{ueip}",
    "MOT:MTR{}{}.HLM": 1000.000000,
    "MOT:MTR{}{}.LLM": -1000.000000,
    "MOT:MTR{}{}_EGUAFTLIMIT_SP": 2.048000,
    "MOT:MTR{}{}_MENCTYPE_CMD": "Reverse Quadrature",
    "MOT:MTR{}{}_AENCTYPE_CMD": "Pulse and Dir",
    "MOT:MTR{}{}_MTRTYPE_CMD": "HA Stepper",
    "MOT:MTR{}{}_ON_CMD": "Off",
    "MOT:MTR{}{}_AUTOONOFF_CMD": "On",
}

CONTROLLER_SETUP = {
    "MOT:DMC{}:SEND_CMD_STR": "CN-1,-1",
    "MOT:DMC{}:LIMITTYPE_CMD": "NO",
    "MOT:DMC{}:HOMETYPE_CMD": "NO",
    "MOT:DMC{}:LIMITTYPE_CMD": "NO",
    "MOT:DMC{}:HOMETYPE_CMD": "NO",
}

# TEST_MODES = [TestModes.DEVSIM,TestModes.NOSIM]
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
            self.ca.assert_that_pv_is("MOT:MTR{}{}.RBV".format(self.controller, motor), 0)

    def stop_motors(self):
        for motor in ["{:02d}".format(mtr) for mtr in range(1, self.num_motors + 1)]:
            self.ca.set_pv_value("MOT:MTR{}{}.STOP".format(self.controller, motor), 1)
            self.ca.assert_that_pv_is("MOT:MTR{}{}.DMOV".format(self.controller, motor), 1)
            self.ca.assert_that_pv_is("MOT:MTR{}{}.MOVN".format(self.controller, motor), 0)

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=None, default_timeout=20, default_wait_time=0.0)
        # test galil hardware does not currently have an encoder, software simulated motors do
        if IOCRegister.test_mode == TestModes.NOSIM:
            ueip = "No"
        else:
            ueip = "Yes"
        self.setup_motors(ueip=ueip)

    def tearDown(self):
        self.stop_motors()

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
        val = 3.0
        self.ca.set_pv_value("MOT:MTR0101", val)
        self.ca.assert_that_pv_is("MOT:MTR0101", val)
        self.ca.assert_that_pv_is("MOT:MTR0101.RBV", val)

    def test_GIVEN_axis_requested_to_move_THEN_axis_moves(self):
        self.zero_motors()

        # Move axis 1
        val = 4.0
        self.ca.set_pv_value("GALIL_01:AXIS1:SP", val)
        self.ca.assert_that_pv_is("GALIL_01:AXIS1:SP:RBV", val)
        self.ca.assert_that_pv_is("GALIL_01:AXIS1", val)
        self.ca.assert_that_pv_is("MOT:MTR0101", val)
        self.ca.assert_that_pv_is("MOT:MTR0101.RBV", val)

    # @skip_always("Not working")
    @skip_if_nosim("No encoder on test real motor")
    def test_GIVEN_motors_THEN_check_motor_encoder_diff_works(self):
        val = 2.0
        # setup motor using encoder
        self.ca.set_pv_value("MOT:MTR0101.UEIP", "Yes")
        self.ca.assert_that_pv_is("MOT:MTR0101.UEIP", "Yes")
        mres = self.ca.get_pv_value("MOT:MTR0101.MRES")
        eres = self.ca.get_pv_value("MOT:MTR0101.ERES")
        self.zero_motors()

        # move to initial position and check in step
        self.ca.set_pv_value("MOT:MTR0101", val, wait=True)
        self.ca.assert_that_pv_is_number("MOT:MTR0101", val)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.RBV", val, tolerance=eres)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.RMP", val / mres, tolerance=mres)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.REP", val / eres, tolerance=eres)
        self.ca.assert_that_pv_is_number("MOT:MTR0101_MTRENC_DIFF", 0.0, tolerance=eres)

        # now double encoder resolution so encoder now thinks it is at 2*val
        # giving difference (val - 2*val)
        self.ca.set_pv_value("MOT:MTR0101.ERES", eres * 2.0, wait=True)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.RMP", val / mres, tolerance=mres)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.REP", val / eres, tolerance=eres)
        self.ca.assert_that_pv_is_number("MOT:MTR0101.RBV", 2.0 * val, tolerance=eres)
        self.ca.assert_that_pv_is_number("MOT:MTR0101_MTRENC_DIFF", -val, tolerance=eres)

    def setup_motors(self, ueip):
        for key, value in CONTROLLER_SETUP.items():
            self.ca.set_pv_value(key.format(self.controller), value)
            self.ca.assert_that_pv_is(key.format(self.controller), value)

        for motor in ["{:02d}".format(mtr) for mtr in range(1, self.num_motors + 1)]:
            for key, value in MOTOR_SETUP.items():
                if isinstance(value, str):
                    value = value.format(ueip=ueip)
                self.ca.set_pv_value(key.format(self.controller, motor), value)
                self.ca.assert_that_pv_is(key.format(self.controller, motor), value)
