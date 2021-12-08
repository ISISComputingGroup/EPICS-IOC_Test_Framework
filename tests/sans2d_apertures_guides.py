import unittest
import os

from genie_python.channel_access_exceptions import WriteAccessException
from parameterized import parameterized

from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.axis import set_axis_moving, assert_axis_not_moving, assert_axis_moving, stop_axis_moving

galil_settings_path = os.path.realpath(
    os.path.join(
        os.getenv("EPICS_KIT_ROOT"), "support", "motorExtensions",
        "master", "settings", "sans2d_apertures_guides"
    )
)

GALIL_ADDR1 = "127.0.0.1"
GALIL_ADDR2 = "127.0.0.2"

ioc_name = "FINS"
fins_settings_path = os.path.join(EPICS_TOP, "ioc", "master", ioc_name, "exampleSettings", "SANS2D_vacuum")
ioc_prefix = "FINS_VAC"

IOCS = [
    {
        "name": "GALILMUL_01",
        "directory": get_default_ioc_dir("GALILMUL"),
        "custom_prefix": "MOT",
        "pv_for_existence": "MTR0101",
        "macros": {
            "MTRCTRL1": "01",
            "GALILADDR1": GALIL_ADDR1,
            "MTRCTRL2": "02",
            "GALILADDR2": GALIL_ADDR2,
            "GALILCONFIGDIR": galil_settings_path.replace("\\", "/"),
        }
    },
    {
        "name": "FINS_01",
        "directory": get_default_ioc_dir(ioc_name),
        "custom_prefix": ioc_prefix,
        "pv_for_existence": "HEARTBEAT",
        "macros": {
            "FINSCONFIGDIR": fins_settings_path.replace("\\", "/"),
            "PLCIP": "127.0.0.3"
        },
    }
]

TEST_MODES = [TestModes.RECSIM]

AXES_TO_STOP = ["APERTURE_{}".format(i) for i in range(1, 6)] + ["GUIDE_{}".format(j) for j in range(1, 6)]


class Sans2dAperturesGuidesTests(unittest.TestCase):
    """
    Tests for the sans2d waveguides and apertures tank motor extensions.
    """

    def setUp(self):
        self.ca = ChannelAccess()


    @parameterized.expand(AXES_TO_STOP)
    def test_GIVEN_move_enabled_axis_moving_WHEN_stop_all_THEN_axis_stopped(self, axis):
        # Set interlock to enabled
        self.ca.set_pv_value("FINS_VAC:SIM:ADDR:1001", 64)
        self.ca.assert_that_pv_is("FINS_VAC:GALIL_INTERLOCK", "CAN MOVE")
        # Stop axis to prevent test instability (other tests may have left it moving)
        stop_axis_moving(axis)
        assert_axis_not_moving(axis)
        # Execute test
        for _ in range(3):
            set_axis_moving(axis)
            assert_axis_moving(axis)
            self.ca.set_pv_value("MOT:SANS2DAPWV:STOP_MOTORS:ALL", 1)
            assert_axis_not_moving(axis)

    @parameterized.expand(AXES_TO_STOP)
    def test_GIVEN_move_disabled_axis_moving_WHEN_stop_all_THEN_axis_not_stopped(self, axis):
        # Set interlock to enabled
        self.ca.set_pv_value("FINS_VAC:SIM:ADDR:1001", 64)
        self.ca.assert_that_pv_is("FINS_VAC:GALIL_INTERLOCK", "CAN MOVE")
        # Execute test
        for _ in range(3):
            set_axis_moving(axis)
            assert_axis_moving(axis)
            self.ca.set_pv_value("FINS_VAC:SIM:ADDR:1001", 0)
            self.ca.assert_that_pv_is("FINS_VAC:GALIL_INTERLOCK", "CANNOT MOVE")
            self.ca.set_pv_value("MOT:SANS2DAPWV:STOP_MOTORS:ALL", 1)
            assert_axis_moving(axis)
            self.ca.set_pv_value("FINS_VAC:SIM:ADDR:1001", 64)
            self.ca.assert_that_pv_is("FINS_VAC:GALIL_INTERLOCK", "CAN MOVE")

    @parameterized.expand(AXES_TO_STOP)
    def test_GIVEN_move_disabled_THEN_all_axis_motion_is_inhibited(self, axis):

        self.ca.set_pv_value("FINS_VAC:SIM:ADDR:1001", 0, wait=True)
        self.ca.assert_that_pv_is("FINS_VAC:GALIL_INTERLOCK", "CANNOT MOVE")
        for _ in range(3):
            self.ca.assert_that_pv_is("MOT:" + axis + ":SP.DISP", "1")
            self.ca.assert_that_pv_is("MOT:" + axis + ":MTR.DISP", "1")

