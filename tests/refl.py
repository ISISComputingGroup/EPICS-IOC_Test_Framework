import os
import unittest
from contextlib import contextmanager
from math import tan, radians

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP, PythonIOCLauncher, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import ManagerMode
from utils.testing import unstable_test
import time


GALIL_ADDR = "128.0.0.0"
INITIAL_VELOCITY = 0.5
MEDIUM_VELOCITY = 2
FAST_VELOCITY = 100
SOFT_LIMIT_HI = 10000
SOFT_LIMIT_LO = -10000

ioc_number = 1
DEVICE_PREFIX = "REFL_{:02d}".format(ioc_number)
GALIL_PREFIX = "GALIL_01"
GALIL_PREFIX_JAWS = "GALIL_02"
test_config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "good_for_refl"))
test_var_path = os.path.join(test_config_path, "var")

IOCS = [
    # Deliberately start the REFL server first to check on waiting for motors functionality
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("REFL", iocnum=ioc_number),
        "started_text": "Instantiating Beamline Model",
        "pv_for_existence": "STAT",
        "macros": {
            "CONFIG_FILE": "config_init.py"
        },
        "environment_vars": {
            "ICPCONFIGROOT": test_config_path,
            "ICPVARDIR": test_var_path,
        }
    },
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
            "MTR0102.VMAX": INITIAL_VELOCITY,
            "MTR0103.VMAX": MEDIUM_VELOCITY,  # Remove s4 as a speed limiting factor
            "MTR0103.VELO": MEDIUM_VELOCITY,  # Remove s4 as a speed limiting factor
            "MTR0104.VMAX": INITIAL_VELOCITY,
            "MTR0105.VMAX": FAST_VELOCITY,  # Remove angle as a speed limiting factor
            "MTR0107.VMAX": FAST_VELOCITY,
            "MTR0104.LLM": SOFT_LIMIT_LO,
            "MTR0104.HLM": SOFT_LIMIT_HI,
            "MTR0105.LLM": SOFT_LIMIT_LO,
            "MTR0105.HLM": SOFT_LIMIT_HI,
            "MTR0107.ERES": 0.001,
            "MTR0107.MRES": 0.001,
        }
    },
    {
        "name": GALIL_PREFIX_JAWS,
        "custom_prefix": "MOT",
        "directory": get_default_ioc_dir("GALIL", iocnum=2),
        "pv_for_existence": "MTR0201",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "2",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
        "inits": {
            "MTR0208.ERES": 0.001,
            "MTR0208.MRES": 0.001
        }
    },
    {
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    },

]


TEST_MODES = [TestModes.DEVSIM]

# Spacing in the config file for the components
SPACING = 2

# This is the position if s3 is out of the beam relative to straight through beam
OUT_POSITION_LOW = -5
OUT_POSITION_HIGH = 5

# Rough tolerance of the motors
MOTOR_TOLERANCE = 0.001


@contextmanager
def all_motors_in_set_mode(channel_access):
    """
    Uses a context to place motor into set mode and ensure that it leaves set mode after context has ended. If it
    can not set the mode correctly will not run the yield. This is used so that all moves are instantaneous.
    Returns:
    """
    calibration_set_pv = "{}.SET"
    offset_freeze_switch_pv = "{}.FOFF"

    all_motors = ["MTR0101", "MTR0102", "MTR0103", "MTR0103", "MTR0104", "MTR0105", "MTR0106", "MTR0107", "MTR0108",
                  "MTR0201", "MTR0202", "MTR0203", "MTR0203", "MTR0204", "MTR0205", "MTR0206", "MTR0207", "MTR0208"]

    for motor in all_motors:
        channel_access.set_pv_value(calibration_set_pv.format(motor), "Set")
        offset_freeze_switch = channel_access.get_pv_value(offset_freeze_switch_pv.format(motor))
        channel_access.set_pv_value(offset_freeze_switch_pv.format(motor), "Frozen")

    try:
        yield
    finally:
        for motor in all_motors:
            channel_access.set_pv_value(calibration_set_pv.format(motor), "Use")
            channel_access.set_pv_value(offset_freeze_switch_pv.format(motor), offset_freeze_switch)


class ReflTests(unittest.TestCase):
    """
    Tests for reflectometry server
    """

    def setUp(self):
        self.start_time = time.time()
        self._ioc = IOCRegister.get_running("refl")
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX, default_wait_time=0.0)
        self.ca_galil = ChannelAccess(default_timeout=30, device_prefix="MOT", default_wait_time=0.0)
        self.ca_cs = ChannelAccess(default_timeout=30, device_prefix="CS", default_wait_time=0.0)
        self.ca_no_prefix = ChannelAccess()
        self.ca_cs.set_pv_value("MOT:STOP:ALL", 1)
        self.ca_cs.assert_that_pv_is("MOT:MOVING", 0, timeout=60)
        with all_motors_in_set_mode(self.ca_galil):
            self.ca.set_pv_value("BL:MODE:SP", "NR")
            self.ca.set_pv_value("PARAM:S1:SP", 0)
            self.ca.set_pv_value("PARAM:SMANGLE:SP_NO_ACTION", 0)
            self.ca.set_pv_value("PARAM:SMOFFSET:SP_NO_ACTION", 0)
            self.ca.set_pv_value("PARAM:SMINBEAM:SP", "OUT")
            self.ca.set_pv_value("PARAM:THETA:SP", 0)
            self.ca.set_pv_value("PARAM:DET_POS:SP", 0)
            self.ca.set_pv_value("PARAM:DET_ANG:SP", 0)
            self.ca.set_pv_value("PARAM:DET_LONG:SP", 0)
            self.ca.set_pv_value("PARAM:S3INBEAM:SP", "IN")
            self.ca.set_pv_value("PARAM:S3:SP", 0)
            self.ca.set_pv_value("PARAM:CHOICE:SP", "MTR0205")
            self.ca_galil.set_pv_value("MTR0207", 0)
            self.ca.set_pv_value("PARAM:NOTINMODE:SP", 0)
            self.ca.set_pv_value("BL:MODE:SP", "NR")
            self.ca.set_pv_value("BL:MOVE", 1)
            self.ca_galil.assert_that_pv_is("MTR0105", 0.0)
            self.ca_cs.assert_that_pv_is("MOT:MOVING", 0, timeout=60)

    def set_up_velocity_tests(self, velocity):
        self.ca_galil.set_pv_value("MTR0102.VELO", velocity)
        self.ca_galil.set_pv_value("MTR0104.VELO", velocity)
        self.ca_galil.set_pv_value("MTR0105.VELO", FAST_VELOCITY)  # Remove angle as a speed limiting factor

    def _check_param_pvs(self, param_name, expected_value):
        self.ca.assert_that_pv_is_number(f"PARAM:{param_name}", expected_value, 0.01)
        self.ca.assert_that_pv_is_number(f"PARAM:{param_name}:SP", expected_value, 0.01)
        self.ca.assert_that_pv_is_number(f"PARAM:{param_name}:SP:RBV", expected_value, 0.01)

    @contextmanager
    def _assert_pv_monitors(self, param_name, expected_value):
        with self.ca.assert_that_pv_monitor_is_number(f"PARAM:{param_name}", expected_value, 0.01), \
             self.ca.assert_that_pv_monitor_is_number(f"PARAM:{param_name}:SP", expected_value, 0.01), \
             self.ca.assert_that_pv_monitor_is_number(f"PARAM:{param_name}:SP:RBV", expected_value, 0.01):
            yield

    def test_GIVEN_loaded_WHEN_read_status_THEN_status_ok(self):
        self.ca.assert_that_pv_is("STAT", "OKAY")

    def test_GIVEN_slit_with_beam_along_z_axis_WHEN_set_value_THEN_read_back_MTR_and_setpoints_moves_to_given_value(self):
        expected_value = 3.0

        self.ca.set_pv_value("PARAM:S1:SP_NO_ACTION", expected_value)
        self.ca.assert_that_pv_is("PARAM:S1:SP_NO_ACTION", expected_value)
        self.ca.set_pv_value("BL:MOVE", 1)

        self.ca.assert_that_pv_is("PARAM:S1:SP:RBV", expected_value)
        self.ca_galil.assert_that_pv_is("MTR0101", expected_value)
        self.ca_galil.assert_that_pv_is("MTR0101.RBV", expected_value)
        self.ca.assert_that_pv_is("PARAM:S1", expected_value)

    def test_GIVEN_slit_with_beam_along_z_axis_WHEN_set_value_THEN_monitors_updated(self):
        expected_value = 3.0

        self.ca.set_pv_value("PARAM:S1:SP_NO_ACTION", expected_value)
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
        self.ca_galil.assert_that_pv_is_number("MTR0104", expected_det_value, 0.01)

        # detector angle faces beam
        self._check_param_pvs("DET_ANG", 0.0)
        expected_det_angle = 2.0 * theta_angle
        self.ca_galil.assert_that_pv_is_number("MTR0105", expected_det_angle, 0.01)

    def test_GIVEN_s3_in_beam_WHEN_disable_THEN_monitor_updates_and_motor_moves_to_out_of_beam_position(self):
        expected_value = "OUT"

        with self.ca.assert_that_pv_monitor_is("PARAM:S3INBEAM", expected_value):
            self.ca.set_pv_value("PARAM:S3INBEAM:SP_NO_ACTION", expected_value)
            self.ca.set_pv_value("BL:MOVE", 1)

        self.ca_galil.assert_that_pv_is("MTR0102", OUT_POSITION_HIGH)

    def test_GIVEN_mode_is_NR_WHEN_change_mode_THEN_monitor_updates_to_new_mode(self):
        expected_value = "POLARISED"

        with self.ca.assert_that_pv_monitor_is("BL:MODE", expected_value), \
             self.ca.assert_that_pv_monitor_is("BL:MODE.VAL", expected_value):
                self.ca.set_pv_value("BL:MODE:SP", expected_value)

    @unstable_test()
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

    def test_GIVEN_motor_velocity_altered_by_move_WHEN_move_completed_THEN_velocity_reverted_to_original_value(self):
        expected = INITIAL_VELOCITY
        self.set_up_velocity_tests(expected)

        self.ca.set_pv_value("PARAM:THETA:SP", 5)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0102.VELO", expected)
        self.ca_galil.assert_that_pv_is("MTR0104.DMOV", 1, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0104.VELO", expected)

    def test_GIVEN_motor_velocity_altered_by_move_WHEN_moving_THEN_velocity_altered(self):
        # Given a known initial velocity, confirm that on a move the velocity has changed for the axes
        self.set_up_velocity_tests(INITIAL_VELOCITY)

        self.ca.set_pv_value("PARAM:THETA:SP", 15)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 0, timeout=10)
        self.ca_galil.assert_that_pv_is_not("MTR0102.VELO", INITIAL_VELOCITY)
        self.ca_galil.assert_that_pv_is("MTR0104.DMOV", 0, timeout=10)
        self.ca_galil.assert_that_pv_is_not("MTR0104.VELO", INITIAL_VELOCITY)

    def test_GIVEN_motor_velocity_altered_by_move_WHEN_move_interrupted_THEN_velocity_reverted_to_original_value(self):
        expected = INITIAL_VELOCITY
        final_position = SPACING
        self.set_up_velocity_tests(expected)

        # move and wait for completion
        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)
        self.ca_galil.set_pv_value("MTR0102.STOP", 1)
        self.ca_galil.set_pv_value("MTR0104.STOP", 1)
        self.ca_galil.set_pv_value("MTR0105.STOP", 1)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=2)
        self.ca_galil.assert_that_pv_is_not_number("MTR0102.RBV", final_position, tolerance=0.1)
        self.ca_galil.assert_that_pv_is("MTR0102.VELO", expected)
        self.ca_galil.assert_that_pv_is("MTR0104.DMOV", 1, timeout=2)
        self.ca_galil.assert_that_pv_is_not_number("MTR0104.RBV", 2 * final_position, tolerance=0.1)
        self.ca_galil.assert_that_pv_is("MTR0104.VELO", expected)

    def test_GIVEN_move_was_issued_while_different_move_already_in_progress_WHEN_move_completed_THEN_velocity_reverted_to_value_before_first_move(self):
        expected = INITIAL_VELOCITY
        self.set_up_velocity_tests(expected)
        self.ca_galil.set_pv_value("MTR0102", -4)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 0, timeout=1)
        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=30)
        self.ca_galil.assert_that_pv_is("MTR0102.VELO", expected)

    def test_GIVEN_move_in_progress_WHEN_modifying_motor_velocity_THEN_velocity_reverted_to_value_before_modified_velocity(self):
        # The by-design behaviour (but maybe not expected by the user) is that if a velocity is sent during a move
        # then we ignore this and restore the cached value we had for the currently issued move.
        initial = INITIAL_VELOCITY
        altered = INITIAL_VELOCITY + 5
        expected = INITIAL_VELOCITY
        self.set_up_velocity_tests(initial)

        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)
        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 0, timeout=1)

        self.ca_galil.set_pv_value("MTR0102.VELO", altered)

        self.ca_galil.assert_that_pv_is("MTR0102.DMOV", 1, timeout=30)
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

        test_in_mode_param_names = ["S1", "S3", "THETA", "DET_POS", "S3INBEAM"]
        test_out_of_mode_params = ["DET_ANG", "THETA_AUTO"]

        for param in test_in_mode_param_names:
            self.ca.assert_that_pv_monitor_is("{}{}{}".format(PARAM_PREFIX, param, IN_MODE_SUFFIX), expected_in_mode_value)

        for param in test_out_of_mode_params:
            self.ca.assert_that_pv_monitor_is("{}{}{}".format(PARAM_PREFIX, param, IN_MODE_SUFFIX), expected_out_of_mode_value)

    def test_GIVEN_jaws_set_to_value_WHEN_change_sp_at_low_level_THEN_jaws_sp_rbv_does_not_change(self):
        expected_gap_in_refl = 0.2
        expected_change_to_gap = 1.0

        self.ca.set_pv_value("PARAM:S1HG:SP", expected_gap_in_refl)
        self.ca.assert_that_pv_is_number("PARAM:S1HG", expected_gap_in_refl, timeout=15, tolerance=MOTOR_TOLERANCE)

        self.ca_galil.set_pv_value("JAWS1:HGAP:SP", expected_change_to_gap)
        self.ca_galil.assert_that_pv_is_number("JAWS1:HGAP", expected_change_to_gap, timeout=15, tolerance=MOTOR_TOLERANCE)

        self.ca.assert_that_pv_is("PARAM:S1HG", expected_change_to_gap)
        self.ca.assert_that_pv_is("PARAM:S1HG:SP:RBV", expected_gap_in_refl)

    @parameterized.expand([("slits", "S1", 30.00), ("multi_component", "THETA", 20.00), ("angle", "DET_ANG", -80.0),
                           ("displacement", "DET_POS", 20.0), ("binary", "S3INBEAM", 0)])
    def test_GIVEN_new_parameter_sp_WHEN_parameter_rbv_changing_THEN_parameter_changing_pv_correct(self, _, param, value):
        expected_value = "YES"
        value = value

        self.ca.set_pv_value("PARAM:{}:SP".format(param), value)
        self.ca.assert_that_pv_is("PARAM:{}:CHANGING".format(param), expected_value)

    @parameterized.expand([("slits", "S1", 500.00), ("multi_component", "THETA", -500.00), ("angle", "DET_ANG", -800.0),
                           ("displacement", "DET_POS", 500.0), ("binary", "S3INBEAM", 0)])
    def test_GIVEN_new_parameter_sp_WHEN_parameter_rbv_not_changing_THEN_parameter_changing_pv_correct(self, _, param, value):
        expected_value = "NO"
        value = value

        self.ca.set_pv_value("PARAM:{}:SP".format(param), value)
        self.ca_cs.set_pv_value("MOT:STOP:ALL", 1)

        self.ca.assert_that_pv_is("PARAM:{}:CHANGING".format(param), expected_value)

    @parameterized.expand([("slits", "S1", 500.00), ("multi_component", "THETA", 500.00), ("angle", "DET_ANG", -800.0),
                           ("displacement", "DET_POS", 500.0), ("binary", "S3INBEAM", "OUT")])
    def test_GIVEN_new_parameter_sp_WHEN_parameter_rbv_outside_of_sp_target_tolerance_THEN_parameter_at_rbv_pv_correct(self, _, param, value):
        expected_value = "NO"
        value = value

        self.ca.set_pv_value("PARAM:{}:SP".format(param), value)
        self.ca_cs.set_pv_value("MOT:STOP:ALL", 1)

        self.ca.assert_that_pv_is("PARAM:{}:RBV:AT_SP".format(param), expected_value)

    @parameterized.expand([("slits", "S1", 0.00), ("multi_component", "THETA", 0.00), ("angle", "DET_ANG", 0.0),
                           ("displacement", "DET_POS", 0.0), ("binary", "S3INBEAM", 1)])
    def test_GIVEN_new_parameter_sp_WHEN_parameter_rbv_within_sp_target_tolerance_THEN_parameter_at_rbv_pv_correct(self, _, param, value):
        expected_value = "YES"
        value = value

        self.ca.set_pv_value("PARAM:{}:SP".format(param), value)
        self.ca_cs.set_pv_value("MOT:STOP:ALL", 1)

        self.ca.assert_that_pv_is("PARAM:{}:RBV:AT_SP".format(param), expected_value)

    def test_GIVEN_a_low_level_beamline_change_WHEN_values_changed_THEN_high_level_parameters_updated(self):
        self.ca_galil.set_pv_value("MTR0102", -400)

        self.ca.assert_that_pv_value_is_changing("PARAM:S3", wait=2)
        self.ca.assert_that_pv_is("PARAM:S3:RBV:AT_SP", "NO")

    def test_GIVEN_engineering_correction_WHEN_move_THEN_move_includes_engineering_correction(self):
        theta = 2
        self.ca.set_pv_value("PARAM:THETA:SP", theta)
        self.ca.set_pv_value("PARAM:S5:SP", 0)

        self.ca.assert_that_pv_is("COR:MOT:MTR0206:DESC",
                                  "Interpolated from file s4_correction.dat on MOT:MTR0206 for s5")
        self.ca.assert_that_pv_is("COR:MOT:MTR0206", theta/10.0)  # s4 correction is a 1/10 of theta

        # soon after movement starts and before movement stops the velocity should be the same
        distance_from_sample_to_s4 = (3.5 - 2.0) * 2
        expected_position = distance_from_sample_to_s4 * tan(radians(theta * 2)) + theta / 10.0
        self.ca_galil.assert_that_pv_is_number("MTR0206.RBV", expected_position, tolerance=MOTOR_TOLERANCE, timeout=30)
        self.ca.assert_that_pv_is_number("PARAM:S5", 0, tolerance=MOTOR_TOLERANCE, timeout=10)

    def test_GIVEN_param_not_in_mode_and_sp_changed_WHEN_performing_beamline_move_THEN_sp_is_applied(self):
        expected = 1.0
        self.ca.set_pv_value("PARAM:NOTINMODE:SP_NO_ACTION", expected)

        self.ca.set_pv_value("BL:MOVE", 1, wait=True)

        self.ca_galil.assert_that_pv_is("MTR0205.DMOV", 1, timeout=10)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE:SP:RBV", expected)
        self.ca.assert_that_pv_is_number("PARAM:NOTINMODE", expected)

    def test_GIVEN_param_not_in_mode_and_sp_changed_WHEN_performing_individual_move_THEN_sp_is_applied(self):
        expected = 1.0
        self.ca.set_pv_value("PARAM:NOTINMODE:SP_NO_ACTION", expected)

        self.ca.set_pv_value("PARAM:NOTINMODE:ACTION", 1, wait=True)

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

        self.ca.set_pv_value("PARAM:NOTINMODE:ACTION", 1, wait=True)

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
        self.ca_galil.set_pv_value("MTR0103.VELO", MEDIUM_VELOCITY)

        self.ca.set_pv_value("PARAM:THETA:SP", 22.5)

        # soon after movement starts and before movement stops the velocity should be the same
        self.ca_galil.assert_that_pv_is("MTR0103.DMOV", 0, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0103.VELO", MEDIUM_VELOCITY, timeout=0.5)
        self.ca_galil.assert_that_pv_is("MTR0103.DMOV", 0, timeout=10)

        # when the movement finishes it should still be the same
        self.ca_galil.assert_that_pv_is("MTR0103.DMOV", 1, timeout=10)
        self.ca_galil.assert_that_pv_is("MTR0103.VELO", MEDIUM_VELOCITY)

    def test_GIVEN_motor_axis_is_angle_WHEN_motor_alarm_status_is_updated_THEN_alarms_propagate_to_correct_parameters_on_component(self):
        expected_severity_code = "MINOR"
        expected_status_code = "HIGH"
        no_alarm_code = "NO_ALARM"

        # Setting High Limit = Low limit produces alarm on 0105 (detector angle)
        self.ca_galil.set_pv_value("MTR0105.HLM", SOFT_LIMIT_LO)

        # detector angle should be in alarm
        self.ca.assert_that_pv_is("PARAM:DET_ANG.STAT", expected_status_code)
        self.ca.assert_that_pv_is("PARAM:DET_ANG.SEVR", expected_severity_code)
        # detector offset is independent and should not be in alarm
        self.ca.assert_that_pv_is("PARAM:DET_POS.STAT", no_alarm_code)
        self.ca.assert_that_pv_is("PARAM:DET_POS.SEVR", no_alarm_code)

        # Setting High Limit back clears alarm
        self.ca_galil.set_pv_value("MTR0105.HLM", SOFT_LIMIT_HI)

        self.ca.assert_that_pv_is("PARAM:DET_ANG.STAT", no_alarm_code)
        self.ca.assert_that_pv_is("PARAM:DET_ANG.SEVR", no_alarm_code)

    def test_GIVEN_motor_axis_is_displacement_WHEN_motor_alarm_status_is_updated_THEN_alarms_propagate_to_correct_parameters_on_component(self):
        expected_severity_code = "MINOR"
        expected_status_code = "HIGH"
        no_alarm_code = "NO_ALARM"

        # Setting High Limit = Low limit produces alarm on 0104 (detector height)
        self.ca_galil.set_pv_value("MTR0104.HLM", SOFT_LIMIT_LO)

        # detector offset should be in alarm
        self.ca.assert_that_pv_is("PARAM:DET_POS.STAT", expected_status_code)
        self.ca.assert_that_pv_is("PARAM:DET_POS.SEVR", expected_severity_code)
        # theta is derived from detector offset and should be in alarm
        self.ca.assert_that_pv_is("PARAM:THETA.STAT", expected_status_code)
        self.ca.assert_that_pv_is("PARAM:THETA.SEVR", expected_severity_code)
        # detector angle is independent and should not be in alarm
        self.ca.assert_that_pv_is("PARAM:DET_ANG.STAT", no_alarm_code)
        self.ca.assert_that_pv_is("PARAM:DET_ANG.SEVR", no_alarm_code)

        # Setting High Limit back clears alarm
        self.ca_galil.set_pv_value("MTR0104.HLM", SOFT_LIMIT_HI)

        self.ca.assert_that_pv_is("PARAM:DET_POS.STAT", no_alarm_code)
        self.ca.assert_that_pv_is("PARAM:DET_POS.SEVR", no_alarm_code)
        self.ca.assert_that_pv_is("PARAM:THETA.STAT", no_alarm_code)
        self.ca.assert_that_pv_is("PARAM:THETA.SEVR", no_alarm_code)

    @parameterized.expand([("Variable", "DET_POS", "MTR0104"), ("Frozen", "DET_POS", "MTR0104"), ("Frozen", "DET_ANG", "MTR0105")])
    def test_GIVEN_motors_not_at_zero_WHEN_define_motor_position_to_THEN_motor_position_is_changed_without_move(self, initial_foff, param_name, motor_name):
        offset = 10
        new_position = 2
        self.ca.set_pv_value("PARAM:{}:SP".format(param_name), offset)
        self.ca_galil.set_pv_value("MTR0104.FOFF", initial_foff)
        self.ca_galil.set_pv_value("MTR0104.OFF", 0)
        self.ca.assert_that_pv_is_number("PARAM:{}".format(param_name), offset, tolerance=MOTOR_TOLERANCE, timeout=30)
        self.ca_galil.assert_that_pv_is("MTR0104.DMOV", 1, timeout=30)

        with ManagerMode(self.ca_no_prefix):
            self.ca.set_pv_value("PARAM:{}:DEFINE_POSITION_AS".format(param_name), new_position)

        # soon after change there should be no movement, ie a move is triggered but the motor itself does not move so it
        # is very quick
        self.ca_galil.assert_that_pv_is("{}.DMOV".format(motor_name), 1, timeout=1)
        self.ca_galil.assert_that_pv_is("{}.RBV".format(motor_name), new_position)
        self.ca_galil.assert_that_pv_is("{}.VAL".format(motor_name), new_position)
        self.ca_galil.assert_that_pv_is("{}.SET".format(motor_name), "Use")
        self.ca_galil.assert_that_pv_is("{}.FOFF".format(motor_name), initial_foff)
        self.ca_galil.assert_that_pv_is_number("{}.OFF".format(motor_name), 0.0, tolerance=MOTOR_TOLERANCE)

        self.ca.assert_that_pv_is("PARAM:{}".format(param_name), new_position)
        self.ca.assert_that_pv_is("PARAM:{}:SP".format(param_name), new_position)
        self.ca.assert_that_pv_is("PARAM:{}:SP_NO_ACTION".format(param_name), new_position)
        self.ca.assert_that_pv_is("PARAM:{}:CHANGED".format(param_name), "NO")
        self.ca.assert_that_pv_is("PARAM:THETA", 0)
        self.ca.assert_that_pv_is("PARAM:THETA:SP", 0)
        self.ca.assert_that_pv_is("PARAM:THETA:SP:RBV", 0)

    def test_GIVEN_jaws_not_at_zero_WHEN_define_motor_position_for_jaw_gaps_THEN_jaws_position_are_changed_without_move(self):
        param_name = "S1VG"
        jaw_motors = ["MTR0201", "MTR0202"]
        initial_gap = 1.0
        initial_centre = 2.0
        new_gap = 4.0
        expected_pos = {"MTR0201": new_gap/2.0 - initial_centre,
                        "MTR0202": new_gap/2.0 + initial_centre}
        self.ca.assert_setting_setpoint_sets_readback(initial_gap, "PARAM:S1VG", expected_alarm=None, timeout=30)
        self.ca.assert_setting_setpoint_sets_readback(initial_centre, "PARAM:S1VC", expected_alarm=None, timeout=30)
        for motor_name in jaw_motors:
            self.ca_galil.set_pv_value("{}.FOFF".format(motor_name), "Frozen")
            self.ca_galil.set_pv_value("{}.OFF".format(motor_name), 0)
        for motor_name in jaw_motors:
            self.ca_galil.assert_that_pv_is("{}.DMOV".format(motor_name), 1, timeout=30)

        with ManagerMode(self.ca_no_prefix):
            self.ca.set_pv_value("PARAM:{}:DEFINE_POSITION_AS".format(param_name), new_gap)

        # soon after change there should be no movement, ie a move is triggered but the motor itself does not move so it
        # is very quick
        for motor_name in jaw_motors:
            self.ca_galil.assert_that_pv_is("{}.DMOV".format(motor_name), 1, timeout=1)

        for motor_name in jaw_motors:
            # jaws are open to half the gap
            self.ca_galil.assert_that_pv_is("{}.RBV".format(motor_name), expected_pos[motor_name])
            self.ca_galil.assert_that_pv_is("{}.VAL".format(motor_name), expected_pos[motor_name])
            self.ca_galil.assert_that_pv_is("{}.SET".format(motor_name), "Use")
            self.ca_galil.assert_that_pv_is("{}.FOFF".format(motor_name), "Frozen")
            self.ca_galil.assert_that_pv_is_number("{}.OFF".format(motor_name), 0.0, tolerance=MOTOR_TOLERANCE)

        self.ca.assert_that_pv_is("PARAM:{}".format(param_name), new_gap)
        self.ca.assert_that_pv_is("PARAM:{}:SP".format(param_name), new_gap)
        self.ca.assert_that_pv_is("PARAM:{}:SP_NO_ACTION".format(param_name), new_gap)
        self.ca.assert_that_pv_is("PARAM:{}:CHANGED".format(param_name), "NO")

    def test_GIVEN_jaws_not_at_zero_WHEN_define_motor_position_for_jaw_centres_THEN_jaws_position_are_changed_without_move(self):
        param_name = "S1HC"
        jaw_motors = ["MTR0203", "MTR0204"]
        initial_gap = 1.0
        initial_centre = 2.0
        new_centre = 4.0
        expected_pos = {"MTR0203": initial_gap/2.0 + new_centre,
                        "MTR0204": initial_gap/2.0 - new_centre}
        self.ca.assert_setting_setpoint_sets_readback(initial_gap, "PARAM:S1HG", expected_alarm=None, timeout=30)
        self.ca.assert_setting_setpoint_sets_readback(initial_centre, "PARAM:S1HC", expected_alarm=None, timeout=30)
        for motor_name in jaw_motors:
            self.ca_galil.set_pv_value("{}.FOFF".format(motor_name), "Frozen")
            self.ca_galil.set_pv_value("{}.OFF".format(motor_name), 0)
        for motor_name in jaw_motors:
            self.ca_galil.assert_that_pv_is("{}.DMOV".format(motor_name), 1, timeout=30)

        with ManagerMode(self.ca_no_prefix):
            self.ca.set_pv_value("PARAM:{}:DEFINE_POSITION_AS".format(param_name), new_centre)

        # soon after change there should be no movement, ie a move is triggered but the motor itself does not move so it
        # is very quick
        for motor_name in jaw_motors:
            self.ca_galil.assert_that_pv_is("{}.DMOV".format(motor_name), 1, timeout=1)

        for motor_name in jaw_motors:
            # jaws are open to half the gap
            self.ca_galil.assert_that_pv_is("{}.RBV".format(motor_name), expected_pos[motor_name])
            self.ca_galil.assert_that_pv_is("{}.VAL".format(motor_name), expected_pos[motor_name])
            self.ca_galil.assert_that_pv_is("{}.SET".format(motor_name), "Use")
            self.ca_galil.assert_that_pv_is("{}.FOFF".format(motor_name), "Frozen")
            self.ca_galil.assert_that_pv_is_number("{}.OFF".format(motor_name), 0.0, tolerance=MOTOR_TOLERANCE)

        self.ca.assert_that_pv_is("PARAM:{}".format(param_name), new_centre)
        self.ca.assert_that_pv_is("PARAM:{}:SP".format(param_name), new_centre)
        self.ca.assert_that_pv_is("PARAM:{}:SP_NO_ACTION".format(param_name), new_centre)
        self.ca.assert_that_pv_is("PARAM:{}:CHANGED".format(param_name), "NO")

    def test_GIVEN_theta_THEN_define_position_as_does_not_exist(self):
        param_name = "THETA"
        self.ca.assert_that_pv_exists("PARAM:{}".format(param_name))
        self.ca.assert_that_pv_does_not_exist("PARAM:{}:DEFINE_POSITION_AS".format(param_name))

    def test_GIVEN_motors_at_zero_WHEN_define_motor_position_to_and_back_multiple_times_THEN_motor_position_is_changed_without_move(self):
        param_name = "DET_POS"
        motor_name = "MTR0104"
        initial_foff = "Frozen"
        self.ca.set_pv_value("PARAM:{}:SP".format(param_name), 0)
        self.ca_galil.set_pv_value("MTR0104.FOFF", initial_foff)
        self.ca_galil.set_pv_value("MTR0104.OFF", 0)
        self.ca.assert_that_pv_is_number("PARAM:{}".format(param_name), 0, tolerance=MOTOR_TOLERANCE, timeout=30)
        self.ca_galil.assert_that_pv_is("MTR0104.DMOV", 1, timeout=30)

        for i in range(20):
            new_position = i - 5
            with ManagerMode(self.ca_no_prefix):
                self.ca.set_pv_value("PARAM:{}:DEFINE_POSITION_AS".format(param_name), new_position)

            # soon after change there should be no movement, ie a move is triggered but the motor itself does not move so it
            # is very quick
            self.ca_galil.assert_that_pv_is("{}.DMOV".format(motor_name), 1, timeout=1)
            self.ca_galil.assert_that_pv_is("{}.RBV".format(motor_name), new_position)
            self.ca_galil.assert_that_pv_is("{}.VAL".format(motor_name), new_position)
            self.ca_galil.assert_that_pv_is("{}.SET".format(motor_name), "Use")
            self.ca_galil.assert_that_pv_is("{}.FOFF".format(motor_name), initial_foff)
            self.ca_galil.assert_that_pv_is_number("{}.OFF".format(motor_name), 0.0, tolerance=MOTOR_TOLERANCE)

            self.ca.assert_that_pv_is("PARAM:{}".format(param_name), new_position)
            self.ca.assert_that_pv_is("PARAM:{}:SP".format(param_name), new_position)
            self.ca.assert_that_pv_is("PARAM:{}:SP_NO_ACTION".format(param_name), new_position)
            self.ca.assert_that_pv_is("PARAM:{}:CHANGED".format(param_name), "NO")

    def test_GIVEN_parameter_not_in_manager_mode_WHEN_define_position_THEN_position_is_not_defined(self):
        new_position = 10

        param_pv = "PARAM:{}:DEFINE_POSITION_AS".format("DET_POS")
        self.assertRaises(IOError, self.ca.set_pv_value, param_pv, new_position)

        self.ca.assert_that_pv_is_not(param_pv, new_position)

    def test_GIVEN_value_parameter_WHEN_read_THEN_value_returned(self):
        param_pv = "CONST:TEN"

        self.ca.assert_that_pv_is(param_pv, 10)
        self.ca.assert_that_pv_is("{}.DESC".format(param_pv), "The value 10")

    def test_GIVEN_bool_parameter_WHEN_read_THEN_value_returned(self):
        param_pv = "CONST:YES"

        self.ca.assert_that_pv_is(param_pv, "YES")

    def test_GIVEN_string_constant_parameter_WHEN_read_THEN_value_returned(self):
        param_pv = "CONST:STRING"

        self.ca.assert_that_pv_is(param_pv, "Test String")

    def test_GIVEN_PNR_mode_with_SM_angle_WHEN_move_in_disable_mode_and_into_PNR_THEN_beamline_is_updated_on_mode_change_and_value_of_pd_offsets_correct(self):
        self.ca.set_pv_value("BL:MODE:SP", "POLARISED")
        self.ca.set_pv_value("PARAM:SMANGLE:SP_NO_ACTION", 0.2)
        self.ca.set_pv_value("BL:MOVE", 1)
        self.ca.assert_that_pv_is_number("PARAM:SMANGLE", 0.2, tolerance=1e-2)

        self.ca.set_pv_value("BL:MODE:SP", "DISABLED")
        self.ca.set_pv_value("PARAM:SMANGLE:SP", 0)
        self.ca.assert_that_pv_is_number("PARAM:SMANGLE", 0.0, tolerance=1e-2)

        self.ca.assert_that_pv_is_number("PARAM:S3", 0.0, tolerance=1e-2)
        self.ca.assert_that_pv_is_number("PARAM:DET_POS", 0.0, tolerance=1e-2)

        self.ca.set_pv_value("BL:MODE:SP", "POLARISED")

        # In polarised mode the sm angle will now make everything appear to be in the wrong place.
        # This test will also check that on changing modes the beamline is updated
        self.ca.assert_that_pv_is_not_number("PARAM:S3", 0.0, tolerance=1e-2)
        self.ca.assert_that_pv_is_not_number("PARAM:DET_POS", 0.0, tolerance=1e-2)

    @parameterized.expand([(0, OUT_POSITION_HIGH), (22.5, OUT_POSITION_LOW)])
    def test_GIVEN_component_with_multiple_parked_positions_WHEN_moving_out_of_beam_THEN_driver_moves_to_correct_out_of_beam_position_based_on_beam_interception(
            self, theta_sp, expected_out_of_beam_position):
        self.ca.assert_that_pv_is("PARAM:S3INBEAM", "IN")

        self.ca.set_pv_value("PARAM:THETA:SP_NO_ACTION", theta_sp, wait=True)
        self.ca.set_pv_value("PARAM:S3INBEAM:SP_NO_ACTION", "OUT", wait=True)
        self.ca.set_pv_value("BL:MOVE", 1, wait=True)

        self.ca_galil.assert_that_pv_is_number("MTR0102.VAL", expected_out_of_beam_position, timeout=5)

    def test_GIVEN_component_with_multiple_out_of_beam_positions_is_out_of_beam_WHEN_beam_intercept_moves_above_threshold_THEN_driver_moves_to_correct_out_of_beam_position(self):
        self.ca.assert_that_pv_is("PARAM:S3INBEAM", "IN")
        self.ca.set_pv_value("PARAM:S3INBEAM:SP", "OUT", wait=True)
        self.ca.assert_that_pv_is("PARAM:S3INBEAM:CHANGING", "NO", timeout=40)
        self.ca_galil.assert_that_pv_is_number("MTR0102.RBV", OUT_POSITION_HIGH, timeout=20)

        self.ca.set_pv_value("PARAM:THETA:SP", 22.5, wait=True)

        self.ca_galil.assert_that_pv_is_number("MTR0102.VAL", OUT_POSITION_LOW, timeout=5)

    @parameterized.expand([(0, OUT_POSITION_HIGH, "OUT"),
                           (0, OUT_POSITION_LOW, "IN"),
                           (22.5, OUT_POSITION_HIGH, "IN"),
                           (22.5, OUT_POSITION_LOW, "OUT")])
    def test_GIVEN_component_with_multiple_parked_positions_WHEN_moving_axis_to_sp_THEN_inbeam_param_reports_correct_rbv(self, theta_sp, axis_sp, expected_inbeam_status):
        self.ca.assert_that_pv_is("PARAM:S3INBEAM", "IN")

        self.ca.set_pv_value("PARAM:THETA:SP", theta_sp, wait=True)
        self.ca.assert_that_pv_is("PARAM:THETA:CHANGING", "NO", timeout=30)

        self.ca_galil.set_pv_value("MTR0102.VAL", axis_sp, wait=True)

        self.ca.assert_that_pv_is("PARAM:S3INBEAM:CHANGING", "NO", timeout=30)
        self.ca.assert_that_pv_is("PARAM:S3INBEAM", expected_inbeam_status)

    def test_GIVEN_driver_with_param_value_dependent_axis_WHEN_set_value_THEN_correct_axis_drives_to_position_and_read_back_is_correct(self):
        expected_offset1 = 0.3
        expected_offset2 = 0.2
        for expected_offset, choice, mot0205, mot0207 in [(expected_offset1, "MTR0207", 0, expected_offset1),
                                                          (expected_offset2, "MTR0205", expected_offset2, expected_offset1)]:
            self.ca.assert_setting_setpoint_sets_readback(choice, "PARAM:CHOICE")
            self.ca.set_pv_value("PARAM:NOTINMODE:SP", expected_offset)

            self.ca.assert_that_pv_is("PARAM:NOTINMODE", expected_offset, timeout=20)
            self.ca_galil.assert_that_pv_is_number("MTR0205.RBV", mot0205, timeout=20)
            self.ca_galil.assert_that_pv_is_number("MTR0207.RBV", mot0207, timeout=20)

    def test_GIVEN_theta_WHEN_detector_long_axis_changes_THEN_detector_tracks(self):
        theta_angle = 2
        long_axis_addition = 1
        self.ca.set_pv_value("PARAM:THETA:SP", theta_angle)
        self.ca.set_pv_value("BL:MOVE", 1)

        # theta set
        self._check_param_pvs("THETA", theta_angle)

        self.ca.set_pv_value("PARAM:DET_LONG:SP", long_axis_addition)
        self.ca.set_pv_value("BL:MOVE", 1)

        expected_det_value = (2 * SPACING + long_axis_addition) * tan(radians(theta_angle * 2.0))

        self._check_param_pvs("DET_LONG", long_axis_addition)
        self._check_param_pvs("DET_POS", 0.0)
        self.ca_galil.assert_that_pv_is_number("MTR0104", expected_det_value, 0.01)
