import os
import unittest
from math import tan, radians

from utils.channel_access import ChannelAccess, MonitorAssertion
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP, PythonIOCLauncher
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"
DEVICE_PREFIX = "REFL"

REFL_PATH = os.path.join(EPICS_TOP, "ISIS", "inst_servers", "master")
GALIL_PREFIX = "GALIL_01"
IOCS = [
    {
        "name": GALIL_PREFIX,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "1",
        },
    },
    {
        "LAUNCHER": PythonIOCLauncher,
        "name": DEVICE_PREFIX,
        "directory": REFL_PATH,
        "python_script_commandline": [os.path.join(REFL_PATH, "ReflectometryServer", "reflectometry_server.py")],
        "started_text": "Reflectometry IOC started",
        "pv_for_existence": "BL:STAT",
        "macros": {
        },
        "environment_vars": {
            "ICPCONFIGROOT": os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "good_for_refl")),
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
        self.ca.set_pv_value("BL:MODE:SP", "NR")
        self.ca.set_pv_value("PARAM:S1:SP", 0)
        self.ca.set_pv_value("PARAM:S3:SP", 0)
        self.ca.set_pv_value("PARAM:THETA:SP", 0)
        self.ca.set_pv_value("PARAM:DET_POS:SP", 0)
        self.ca.set_pv_value("PARAM:DET_ANG:SP", 0)
        self.ca.set_pv_value("PARAM:S3_ENABLED:SP", "IN")
        self.ca.set_pv_value("BL:MOVE", 1)
        self.ca.set_pv_value("BL:MODE:SP", "NR")
        self.ca_galil.assert_that_pv_is("MTR0104", 0.0)

    def test_GIVEN_loaded_WHEN_read_status_THEN_status_ok(self):
        self.ca.assert_that_pv_is("BL:STAT", "OKAY")

    def test_GIVEN_slit_with_beam_along_z_axis_WHEN_set_value_THEN_read_back_MTR_and_setpoints_moves_to_given_value(self):
        expected_value = 3.0

        self.ca.set_pv_value("PARAM:S1:SP_NO_MOVE", expected_value)
        self.ca.assert_that_pv_is("PARAM:S1:SP_NO_MOVE", expected_value)
        self.ca.set_pv_value("BL:MOVE", 1)

        self.ca.assert_that_pv_is("PARAM:S1:SP:RBV", expected_value)
        self.ca_galil.assert_that_pv_is("MTR0101", expected_value)
        self.ca_galil.assert_that_pv_is("MTR0101.RBV", expected_value)
        self.ca.assert_that_pv_is("PARAM:S1", expected_value)

    def test_GIVEN_slit_with_beam_along_z_axis_WHEN_set_value_THEN_monitors_updated(self):
        expected_value = 3.0

        self.ca.set_pv_value("PARAM:S1:SP_NO_MOVE", expected_value)
        self.ca.set_pv_value("BL:MOVE", 1)
        self.ca.assert_that_pv_monitor_is("PARAM:S1", expected_value)

    def test_GIVEN_theta_with_detector_and_slits3_WHEN_set_theta_THEN_values_are_all_correct_rbvs_updated_via_monitors_and_are_available_via_gets(self):
        theta_angle = 2
        self.ca.set_pv_value("PARAM:THETA:SP", theta_angle)

        self.ca.set_pv_value("BL:MOVE", 1)

        # s1 not moved
        self._check_param_pvs("S1", 0.0)
        self.ca_galil.assert_that_pv_is_number("MTR0101", 0.0, 0.01)

        # s3 moved in line
        self._check_param_pvs("S3", 0.0)
        expected_s3_value = SPACING * tan(radians(theta_angle * 2.0))
        self.ca_galil.assert_that_pv_is_number("MTR0102", expected_s3_value, 0.01)

        # theta set
        self._check_param_pvs("THETA", theta_angle)

        # detector moved in line
        self._check_param_pvs("DET_POS", 0.0)
        expected_det_value = 2 * SPACING * tan(radians(theta_angle * 2.0))
        self.ca_galil.assert_that_pv_is_number("MTR0103", expected_det_value, 0.01)

        # detector angle faces beam
        self._check_param_pvs("DET_POS", 0.0)
        expected_det_angle = 2.0 * theta_angle
        self.ca_galil.assert_that_pv_is_number("MTR0104", expected_det_angle, 0.01)

    def _check_param_pvs(self, param_name, expected_s1_value):
        self.ca.assert_that_pv_monitor_is_number("PARAM:%s" % param_name, expected_s1_value, 0.01)
        self.ca.assert_that_pv_is_number("PARAM:%s" % param_name, expected_s1_value, 0.01)
        self.ca.assert_that_pv_monitor_is_number("PARAM:%s:SP" % param_name, expected_s1_value, 0.01)
        self.ca.assert_that_pv_is_number("PARAM:%s:SP" % param_name, expected_s1_value, 0.01)
        self.ca.assert_that_pv_monitor_is_number("PARAM:%s:SP:RBV" % param_name, expected_s1_value, 0.01)
        self.ca.assert_that_pv_is_number("PARAM:%s:SP:RBV" % param_name, expected_s1_value, 0.01)

    def test_GIVEN_enabled_s3_WHEN_disable_THEN_monitor_updates_and_motor_moves_to_disable_position(self):
        expected_value = "OUT"

        self.ca.set_pv_value("PARAM:S3_ENABLED:SP_NO_MOVE", expected_value)
        self.ca.set_pv_value("BL:MOVE", 1)
        self.ca.assert_that_pv_monitor_is("PARAM:S3_ENABLED", expected_value)
        self.ca_galil.assert_that_pv_is("MTR0102", OUT_POSITION)

    def test_GIVEN_mode_is_NR_WHEN_change_mode_THEN_monitor_updates_to_new_mode(self):
        expected_value = "POLERISED"

        mode_monitor = MonitorAssertion(self.ca, "BL:MODE")
        mode_val_monitor = MonitorAssertion(self.ca, "BL:MODE.VAL")
        self.ca.set_pv_value("BL:MODE:SP", expected_value)

        self.ca.assert_that_pv_monitor_is("", expected_value, value_from=mode_monitor)
        self.ca.assert_that_pv_monitor_is("", expected_value, value_from=mode_val_monitor)
