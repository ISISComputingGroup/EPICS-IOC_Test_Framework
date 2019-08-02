import os
import unittest
import time
from contextlib import contextmanager
from math import tan, radians

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP, PythonIOCLauncher
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"
DEVICE_PREFIX = "REFL"
OUT_COMP_INIT_POS = -2.0
IN_COMP_INIT_POS = 1.0
DET_INIT_POS = 5.0
DET_INIT_POS_AUTOSAVE = 1.0
INITIAL_VELOCITY = 0.5
FAST_VELOCITY = 100

REFL_PATH = os.path.join(EPICS_TOP, "ISIS", "inst_servers", "master")
GALIL_PREFIX = "GALIL_01"
test_config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "refl_init"))
IOCS = [
    {
        "name": GALIL_PREFIX,
        "custom_prefix": "MOT",
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "MOT:MTR0101",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "1",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
        "inits": {
            "MTR0102.VMAX": INITIAL_VELOCITY,
            "MTR0103.VMAX": INITIAL_VELOCITY,
            "MTR0104.VMAX": FAST_VELOCITY,  # Remove angle as a speed limiting factor
            "MTR0105.VAL": OUT_COMP_INIT_POS,
            "MTR0106.VAL": IN_COMP_INIT_POS,
            "MTR0107.VAL": DET_INIT_POS
        }
    },
    {
        "ioc_launcher_class": PythonIOCLauncher,
        "name": DEVICE_PREFIX,
        "directory": REFL_PATH,
        "python_script_commandline": [os.path.join(REFL_PATH, "ReflectometryServer", "reflectometry_server.py")],
        "started_text": "Reflectometry IOC started",
        "pv_for_existence": "BL:STAT",
        "macros": {
        },
        "environment_vars": {
            "ICPCONFIGROOT": test_config_path,
            "ICPVARDIR": test_config_path,
        }
    },


]


TEST_MODES = [TestModes.DEVSIM]

# Spacing in the config file for the components
SPACING = 2

# This is the position if s3 is out of the beam relative to straight through beam
OUT_POSITION = -5


class ReflTests(unittest.TestCase):
    """
    Tests for reflectometry server
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("refl")
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca_galil = ChannelAccess(default_timeout=30, device_prefix="MOT")
        self.ca_galil.assert_that_pv_is("MTR0104", 0.0)

    def set_up_velocity_tests(self, velocity):
        self.ca_galil.set_pv_value("MTR0102.VELO", velocity)
        self.ca_galil.set_pv_value("MTR0103.VELO", velocity)
        self.ca_galil.set_pv_value("MTR0104.VELO", FAST_VELOCITY)  # Remove angle as a speed limiting factor

    def _check_param_pvs(self, param_name, expected_value):
        self.ca.assert_that_pv_is_number("PARAM:%s" % param_name, expected_value, 0.01)
        self.ca.assert_that_pv_is_number("PARAM:%s:SP" % param_name, expected_value, 0.01)
        self.ca.assert_that_pv_is_number("PARAM:%s:SP:RBV" % param_name, expected_value, 0.01)

    @contextmanager
    def _assert_pv_monitors(self, param_name, expected_value):
        with self.ca.assert_that_pv_monitor_is_number("PARAM:%s" % param_name, expected_value, 0.01), \
             self.ca.assert_that_pv_monitor_is_number("PARAM:%s:SP" % param_name, expected_value, 0.01), \
             self.ca.assert_that_pv_monitor_is_number("PARAM:%s:SP:RBV" % param_name, expected_value, 0.01):
            yield

    def test_WHEN_ioc_started_up_THEN_rbvs_are_initialised_to_motor_values(self):
        self.ca.assert_that_pv_is("PARAM:IN_POS", IN_COMP_INIT_POS)
        self.ca.assert_that_pv_is("PARAM:OUT_POS", OUT_COMP_INIT_POS)

    def test_GIVEN_theta_init_to_non_zero_and_det_pos_not_autosaved_WHEN_initialising_det_pos_THEN_det_pos_sp_is_initialised_to_rbv_minus_offset_from_theta(self):
        expected_value = DET_INIT_POS - SPACING  # angle between theta component and detector is 45 deg

        self.ca.assert_that_pv_is_number("PARAM:INIT:SP:RBV", expected_value)

    def test_GIVEN_theta_is_non_zero_and_param_is_autosaved_WHEN_initialising_detector_height_param_THEN_param_sp_is_initialised_to_autosave_value(self):
        expected_value = DET_INIT_POS_AUTOSAVE

        self.ca.assert_that_pv_is_number("PARAM:INIT_AUTO:SP:RBV", expected_value)

    def test_GIVEN_component_out_of_beam_WHEN_starting_up_ioc_THEN_inbeam_sp_false_and_pos_sp_zero(self):
        expected_inbeam = "OUT"
        expected_pos = 0.0

        self.ca.assert_that_pv_is("PARAM:IS_OUT:SP:RBV", expected_inbeam)
        self.ca.assert_that_pv_is("PARAM:OUT_POS:SP:RBV", expected_pos)

    def test_GIVEN_component_in_beam_WHEN_starting_up_ioc_THEN_inbeam_sp_true_and_pos_sp_accurate(self):
        expected_inbeam = "IN"
        expected_pos = IN_COMP_INIT_POS

        self.ca.assert_that_pv_is("PARAM:IS_IN:SP:RBV", expected_inbeam)
        self.ca.assert_that_pv_is("PARAM:IN_POS:SP:RBV", expected_pos)

    def test_GIVEN_motor_values_set_WHEN_starting_refl_ioc_THEN_parameter_rbvs_are_initialised_correctly(self):
        expected = IN_COMP_INIT_POS

        self.ca.assert_that_pv_is("PARAM:IN_POS", expected)
