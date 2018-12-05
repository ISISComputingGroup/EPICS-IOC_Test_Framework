import os
import unittest
from math import tan, radians

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import parameterized_list
from parameterized import parameterized

GALIL_ADDR = "128.0.0.0"
DEVICE_PREFIX = "REFL"

REFL_PATH = os.path.join(EPICS_TOP, "ISIS", "inst_servers", "master")
GALIL_PREFIX = "GALIL_01"
IOCS = [
    {
        "name": GALIL_PREFIX,
        "directory": get_default_ioc_dir("GALIL"),
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "1",
        },
    },
    {
        "name": DEVICE_PREFIX,
        "directory": REFL_PATH,
        "ioc_run_commandline": [r"c:\instrument\apps\python\python.exe",
                                os.path.join(REFL_PATH, "ReflectometryServer", "reflectometry_server.py")],
        "started_text": "Reflectometry IOC starter",
        "pv_for_existence": "BL:STAT",
        "macros": {
        },
        "environment_vars": {
            "ICPCONFIGROOT": os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "good_for_refl")),
            "PYTHONUNBUFFERED": "TRUE",
            "EPICS_CAS_INTF_ADDR_LIST": "127.0.0.1",
            "EPICS_CAS_BEACON_ADDR_LIST": "127.255.255.255"
        }
    },


]


TEST_MODES = [TestModes.DEVSIM]

# Spacing in the config file for the components
SPACING = 2


class ReflTests(unittest.TestCase):

    """
    Tests for vertical jaws
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
        self.ca.set_pv_value("BL:MOVE", 1)
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

    def test_GIVEN_theta_with_detector_and_slits3_WHEN_set_theta_THEN_values_are_all_correct_rbvs_updated_via_monitorsand_gets(self):
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

