import json
import os
import unittest
from contextlib import contextmanager

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"
OUT_COMP_INIT_POS = -2.0
IN_COMP_INIT_POS = 1.0
DET_INIT_POS = 5.0
DET_INIT_POS_AUTOSAVE = 1.0
FAST_VELOCITY = 10

ioc_number = 1
DEVICE_PREFIX = "REFL_{:02d}".format(ioc_number)
GALIL_PREFIX = "GALIL_01"
test_config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "good_for_refl"))
test_var_path = os.path.join(test_config_path, "var_init")

REFL_MACROS = json.dumps({"CONFIG_FILE": "config_init.py",  # tested implicitly by entire suite
                          "OPTIONAL_1": "True",
                          "OPTIONAL_2": "False", })

IOCS = [
    {
        "name": GALIL_PREFIX,
        "custom_prefix": "MOT",
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "MTR0101",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "1",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
        "inits": {
            "MTR0101.VMAX": FAST_VELOCITY,
            "MTR0102.VMAX": FAST_VELOCITY,
            "MTR0103.VMAX": FAST_VELOCITY,
            "MTR0101.VAL": OUT_COMP_INIT_POS,
            "MTR0102.VAL": IN_COMP_INIT_POS,
            "MTR0103.VAL": DET_INIT_POS
        }
    },
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("REFL", iocnum=ioc_number),
        "started_text": "Reflectometry IOC started",
        "pv_for_existence": "STAT",
        "environment_vars": {
            "REFL_MACROS": REFL_MACROS,
            "IOC_TEST": "1",
            "ICPCONFIGROOT": test_config_path,
            "ICPVARDIR": test_var_path,
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

    def test_GIVEN_optional_macro_is_set_to_true_THEN_true_value_passed_into_reflectometry_config(self):
        # See macro values in IOC dict above
        self.ca.assert_that_pv_exists("CONST:OPTIONAL_1")

    def test_GIVEN_optional_macro_is_set_to_false_THEN_false_value_passed_into_reflectometry_config(self):
        # See macro values in IOC dict above
        self.ca.assert_that_pv_does_not_exist("CONST:OPTIONAL_2")
