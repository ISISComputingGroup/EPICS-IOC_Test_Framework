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
MEDIUM_VELOCITY = 2
FAST_VELOCITY = 100

REFL_PATH = os.path.join(EPICS_TOP, "ISIS", "inst_servers", "master")
GALIL_PREFIX = "GALIL_01"
GALIL_PREFIX_JAWS = "GALIL_02"
test_config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "good_for_refl"))
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
        "name": GALIL_PREFIX_JAWS,
        "custom_prefix": "MOT",
        "directory": get_default_ioc_dir("GALIL", iocnum=2),
        "pv_for_existence": "MOT:MTR0201",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "2",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
        "inits": {
            "MTR0206.VMAX": MEDIUM_VELOCITY,  # Remove s4 as a speed limiting factor
            "MTR0206.VELO": MEDIUM_VELOCITY,  # Remove s4 as a speed limiting factor
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
        self.ca.set_pv_value("BL:MODE:SP", "NR")
        self.ca.set_pv_value("PARAM:S1:SP", 0)
        self.ca.set_pv_value("PARAM:S3:SP", 0)
        self.ca.set_pv_value("PARAM:THETA:SP", 0)
        self.ca.set_pv_value("PARAM:DET_POS:SP", 0)
        self.ca.set_pv_value("PARAM:DET_ANG:SP", 0)
        self.ca.set_pv_value("PARAM:S3_ENABLED:SP", "IN")
        self.ca.set_pv_value("PARAM:NOTINMODE:SP", 0)
        self.ca.set_pv_value("BL:MODE:SP", "NR")
        self.ca.set_pv_value("BL:MOVE", 1)
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

        expected_s3_value = SPACING * tan(radians(theta_angle * 2.0))

        with self._assert_pv_monitors("S1", 0.0), \
             self._assert_pv_monitors("S3", 0.0), \
             self._assert_pv_monitors("THETA", theta_angle), \
             self._assert_pv_monitors("DET_POS", 0.0), \
             self._assert_pv_monitors("DET_ANG", 0.0):

            self.ca.set_pv_value("BL:MOVE", 1)

        # s1 not moved
        self._check_param_pvs("S1", 0.0)
        self.ca_galil.assert_that_pv_is_number("MTR0101", 0.0, 0.01)

        # s3 moved in line
        self._check_param_pvs("S3", 0.0)
        self.ca_galil.assert_that_pv_is_number("MTR0102", expected_s3_value, 0.01)

        # theta set
        self._check_param_pvs("THETA", theta_angle)

        # detector moved in line
        self._check_param_pvs("DET_POS", 0.0)
        expected_det_value = 2 * SPACING * tan(radians(theta_angle * 2.0))
        self.ca_galil.assert_that_pv_is_number("MTR0103", expected_det_value, 0.01)

        # detector angle faces beam
        self._check_param_pvs("DET_ANG", 0.0)
        expected_det_angle = 2.0 * theta_angle
        self.ca_galil.assert_that_pv_is_number("MTR0104", expected_det_angle, 0.01)

    def test_GIVEN_enabled_s3_WHEN_disable_THEN_monitor_updates_and_motor_moves_to_disable_position(self):
        expected_value = "OUT"

        with self.ca.assert_that_pv_monitor_is("PARAM:S3_ENABLED", expected_value):
            self.ca.set_pv_value("PARAM:S3_ENABLED:SP_NO_MOVE", expected_value)
            self.ca.set_pv_value("BL:MOVE", 1)

        self.ca_galil.assert_that_pv_is("MTR0102", OUT_POSITION)

    def test_GIVEN_mode_is_NR_WHEN_change_mode_THEN_monitor_updates_to_new_mode(self):
        expected_value = "POLARISED"

        with self.ca.assert_that_pv_monitor_is("BL:MODE", expected_value), \
             self.ca.assert_that_pv_monitor_is("BL:MODE.VAL", expected_value):
                self.ca.set_pv_value("BL:MODE:SP", expected_value)

    def test_GIVEN_new_parameter_setpoint_WHEN_triggering_move_THEN_SP_is_only_set_on_motor_when_difference_above_motor_resolution(self):
        target_mres = 0.001
        pos_above_res = 0.01
        pos_below_res = pos_above_res + 0.0001
        self.ca_galil.set_pv_value("MTR0101.MRES", target_mres)

        with self.ca_galil.assert_that_pv_monitor_is_number("MTR0101.VAL", pos_above_res), \
             self.ca_galil.assert_that_pv_monitor_is_number("MTR0101.RBV", pos_above_res):

            self.ca.set_pv_value("PARAM:S1:SP", pos_above_res)

        with self.ca_galil.assert_that_pv_monitor_is_number("MTR0101.VAL", pos_above_res), \
             self.ca_galil.assert_that_pv_monitor_is_number("MTR0101.RBV", pos_above_res):

            self.ca.set_pv_value("PARAM:S1:SP", pos_below_res)

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

    def test_GIVEN_motor_velocity_altered_by_move_WHEN_move_completed_THEN_velocity_reverted_to_original_value(self):
        expected = INITIAL_VELOCITY
        self.set_up_velocity_tests(expected)

        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0102.VELO", expected)
        self.ca_galil.assert_that_pv_is("MTR0103.DMOV", 1, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0103.VELO", expected)

    def test_GIVEN_motor_velocity_altered_by_move_WHEN_move_interrupted_THEN_velocity_reverted_to_original_value(self):
        expected = INITIAL_VELOCITY
        final_position = SPACING
        self.set_up_velocity_tests(expected)

        # move and wait for completion
        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)
        self.ca_galil.set_pv_value("MTR0102.STOP", 1)
        self.ca_galil.set_pv_value("MTR0103.STOP", 1)
        self.ca_galil.set_pv_value("MTR0104.STOP", 1)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=2)
        self.ca_galil.assert_that_pv_is_not_number("MTR0102.RBV", final_position, tolerance=0.1)
        self.ca_galil.assert_that_pv_is("MTR0102.VELO", expected)
        self.ca_galil.assert_that_pv_is("MTR0103.DMOV", 1, timeout=2)
        self.ca_galil.assert_that_pv_is_not_number("MTR0103.RBV", 2 * final_position, tolerance=0.1)
        self.ca_galil.assert_that_pv_is("MTR0103.VELO", expected)

    def test_GIVEN_move_was_issued_while_different_move_already_in_progress_WHEN_move_completed_THEN_velocity_reverted_to_value_before_first_move(self):
        expected = INITIAL_VELOCITY
        self.set_up_velocity_tests(expected)
        self.ca_galil.set_pv_value("MTR0102", -4)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 0, timeout=1)
        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=15)
        self.ca_galil.assert_that_pv_is("MTR0102.VELO", expected)

    def test_GIVEN_move_in_progress_WHEN_modifying_motor_velocity_THEN_motor_retains_new_value_after_move_completed(self):
        initial = INITIAL_VELOCITY
        expected = INITIAL_VELOCITY / 2.0
        self.set_up_velocity_tests(initial)

        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)
        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 0, timeout=1)
        self.ca_galil.set_pv_value("MTR0102.VELO", expected)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0102.VELO", expected)

    def test_GIVEN_mode_is_NR_WHEN_change_mode_THEN_monitor_updates_to_new_mode_and_PVs_inmode_are_labeled_as_such(self):
        
        expected_mode_value = "TESTING"
        PARAM_PREFIX = "PARAM:"
        IN_MODE_SUFFIX = ":IN_MODE"
        expected_in_mode_value = "YES"
        expected_out_of_mode_value = "NO"

        with self.ca.assert_that_pv_monitor_is("BL:MODE", expected_mode_value), \
             self.ca.assert_that_pv_monitor_is("BL:MODE.VAL", expected_mode_value):
                self.ca.set_pv_value("BL:MODE:SP", expected_mode_value)

        test_in_mode_param_names = ["S1", "S3", "THETA", "DET_POS", "S3_ENABLED"]
        test_out_of_mode_params = ["DET_ANG", "THETA_AUTO"]

        for param in test_in_mode_param_names:
            self.ca.assert_that_pv_monitor_is("{}{}{}".format(PARAM_PREFIX, param, IN_MODE_SUFFIX), expected_in_mode_value)
        
        for param in test_out_of_mode_params:
            self.ca.assert_that_pv_monitor_is("{}{}{}".format(PARAM_PREFIX, param, IN_MODE_SUFFIX), expected_out_of_mode_value)

    def test_GIVEN_jaws_set_to_value_WHEN_change_sp_at_low_level_THEN_jaws_sp_rbv_does_not_change(self):

        expected_gap_in_refl = 0.2
        expected_change_to_gap = 1.0

        time.sleep(5)
        self.ca.assert_setting_setpoint_sets_readback(readback_pv="PARAM:S1HG", value=expected_gap_in_refl, expected_alarm=None)

        self.ca_galil.assert_setting_setpoint_sets_readback(readback_pv="JAWS1:HGAP", value=expected_change_to_gap)

        self.ca.assert_that_pv_is("PARAM:S1HG", expected_change_to_gap)
        self.ca.assert_that_pv_is("PARAM:S1HG:SP:RBV", expected_gap_in_refl)

    def test_GIVEN_param_not_in_mode_and_sp_changed_WHEN_performing_beamline_move_THEN_sp_is_applied(self):
        expected = 1.0
        self.ca.set_pv_value("PARAM:NOTINMODE:SP_NO_MOVE", expected)

        self.ca.set_pv_value("BL:MOVE", 1, wait=True)

        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP:RBV", expected)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", expected)

    def test_GIVEN_param_not_in_mode_and_sp_changed_WHEN_performing_individual_move_THEN_sp_is_applied(self):
        expected = 1.0
        self.ca.set_pv_value("PARAM:NOTINMODE:SP_NO_MOVE", expected)

        self.ca.set_pv_value("PARAM:NOTINMODE:MOVE", 1, wait=True)

        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP:RBV", expected)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", expected)

    def test_GIVEN_param_not_in_mode_and_sp_changed_WHEN_performing_individual_move_on_other_param_THEN_no_value_applied(self):
        param_sp = 0.0
        motor_pos = 1.0
        self.ca.set_pv_value("PARAM:NOTINMODE:SP", param_sp)
        self.ca_galil.set_pv_value("MTR0205", motor_pos, wait=True)
        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", motor_pos)

        self.ca.set_pv_value("PARAM:THETA:SP", 0.2, wait=True)
        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP", param_sp)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP:RBV", param_sp)
        self.ca_galil.assert_that_pv_is_number("MTR0205", motor_pos)

    def test_GIVEN_param_not_in_mode_and_sp_unchanged_WHEN_performing_beamline_move_THEN_no_value_applied(self):
        param_sp = 0.0
        motor_pos = 1.0
        self.ca_galil.set_pv_value("MTR0205", motor_pos, wait=True)
        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", motor_pos)

        self.ca.set_pv_value("BL:MOVE", 1, wait=True)

        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP", param_sp)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP:RBV", param_sp)
        self.ca_galil.assert_that_pv_is_number("MTR0205", motor_pos)

    def test_GIVEN_param_not_in_mode_and_sp_unchanged_WHEN_performing_individual_move_THEN_sp_is_applied(self):
        param_sp = 0.0
        motor_pos = 1.0
        self.ca_galil.set_pv_value("MTR0205", motor_pos, wait=True)
        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", motor_pos)

        self.ca.set_pv_value("PARAM:NOTINMODE:MOVE", 1, wait=True)

        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP", param_sp)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP:RBV", param_sp)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", param_sp)

    def test_GIVEN_param_not_in_mode_and_sp_unchanged_WHEN_performing_individual_move_on_other_param_THEN_no_value_applied(self):
        param_sp = 0.0
        motor_pos = 1.0
        self.ca_galil.set_pv_value("MTR0205", motor_pos, wait=True)
        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", motor_pos)

        self.ca.set_pv_value("PARAM:THETA:SP", 0.2, wait=True)

        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP", param_sp)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP:RBV", param_sp)
        self.ca_galil.assert_that_pv_is_number("MTR0205", motor_pos)

    def test_GIVEN_non_synchronised_axis_WHEN_move_which_should_change_velocity_THEN_velocity_not_changed(self):
        self.ca_galil.set_pv_value("MTR0206.VELO", MEDIUM_VELOCITY)

        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)

        # soon after movement starts and before movement stops the velocity should be the same
        self.ca_galil.assert_that_pv_is("MTR0206.DMOV", 0, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0206.VELO", MEDIUM_VELOCITY, timeout=0.5)
        self.ca_galil.assert_that_pv_is("MTR0206.DMOV", 0, timeout=10)

        # when the movement finishes it should still be the same
        self.ca_galil.assert_that_pv_is("MTR0206.DMOV", 1, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0206.VELO", MEDIUM_VELOCITY)
