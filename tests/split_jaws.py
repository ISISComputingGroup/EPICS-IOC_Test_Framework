import unittest
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list
from parameterized import parameterized

MTR_01 = "GALIL_01"
MTR_02 = "GALIL_02"

# PV names for motors
JAWS_BASE_PV = "MOT:JAWS1"
DIRECTIONS = ["N", "S", "E", "W"]

# PV names for GALIL motors
UNDERLYING_MTR_NORTH = "MOT:MTR0101"
UNDERLYING_MTR_SOUTH = "MOT:MTR0102"
UNDERLYING_MTR_EAST = "MOT:MTR0201"
UNDERLYING_MTR_WEST = "MOT:MTR0202"

UNDERLYING_AXES = [UNDERLYING_MTR_NORTH, UNDERLYING_MTR_SOUTH, UNDERLYING_MTR_EAST, UNDERLYING_MTR_WEST]

# Tests will fail if JAWS support module is not up to date and built
test_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "motor_test"))

IOCS = [
    {
        "name": MTR_01,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
    {
        "name": MTR_02,
        "directory": get_default_ioc_dir("GALIL", iocnum=2),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "02",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
]


TEST_MODES = [TestModes.DEVSIM]

TEST_POSITIONS = [-5, 0, 10, 10e-1]


class SplitJawsTests(unittest.TestCase):

    """
    Tests for vertical jaws
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("jaws")
        self.ca = ChannelAccess(default_timeout=30)
        for axis in UNDERLYING_AXES:
            self.ca.set_pv_value("{}.VMAX".format(axis), 100)
            self.ca.set_pv_value("{}.VELO".format(axis), 100)

    def test_GIVEN_ioc_started_THEN_north_underlying_mtr_fields_can_be_read(self):
        expected = self.ca.get_pv_value("{}.VELO".format(UNDERLYING_MTR_NORTH))
        north_pv = "{}:JN".format(JAWS_BASE_PV)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(north_pv))

        self.assertEqual(expected, actual)

    def test_GIVEN_ioc_started_THEN_south_underlying_mtr_fields_can_be_read(self):
        expected = self.ca.get_pv_value("{}.VELO".format(UNDERLYING_MTR_SOUTH))
        south_pv = "{}:JS".format(JAWS_BASE_PV)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(south_pv))

        self.assertEqual(expected, actual)

    def test_GIVEN_ioc_started_THEN_east_underlying_mtr_fields_can_be_read(self):
        expected = self.ca.get_pv_value("{}.VELO".format(UNDERLYING_MTR_EAST))
        east_pv = "{}:JE".format(JAWS_BASE_PV)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(east_pv))

        self.assertEqual(expected, actual)

    def test_GIVEN_ioc_started_THEN_west_underlying_mtr_fields_can_be_read(self):
        expected = self.ca.get_pv_value("{}.VELO".format(UNDERLYING_MTR_WEST))
        west_pv = "{}:JW".format(JAWS_BASE_PV)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(west_pv))

        self.assertEqual(expected, actual)

    @parameterized.expand(parameterized_list(TEST_POSITIONS))
    def test_WHEN_jaw_blade_setpoint_changed_THEN_jaw_blade_moves(self, _, value):
        for direction in DIRECTIONS:
            rbv_pv = "{}:J{}".format(JAWS_BASE_PV, direction)
            sp_pv = "{}:J{}:SP".format(JAWS_BASE_PV, direction)
            self.ca.assert_setting_setpoint_sets_readback(value, rbv_pv, sp_pv)

    def test_GIVEN_jaws_closed_at_centre_WHEN_vgap_opened_THEN_north_and_south_jaws_move(self):
        n_pv = "{}:JN".format(JAWS_BASE_PV)
        s_pv = "{}:JS".format(JAWS_BASE_PV)
        # GIVEN
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0)
        # WHEN
        self.ca.set_pv_value("MOT:JAWS1:VGAP:SP", 1)
        # THEN
        self.ca.assert_that_pv_is(n_pv, 0.5)
        self.ca.assert_that_pv_is(s_pv, -0.5)

    def test_GIVEN_jaws_closed_at_centre_WHEN_hgap_opened_THEN_east_and_west_jaws_move(self):
        e_pv = "{}:JE".format(JAWS_BASE_PV)
        w_pv = "{}:JW".format(JAWS_BASE_PV)
        # GIVEN
        self.ca.assert_that_pv_is("MOT:JAWS1:HGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:HCENT", 0)
        # WHEN
        self.ca.set_pv_value("MOT:JAWS1:HGAP:SP", 1)
        # THEN
        self.ca.assert_that_pv_is(e_pv, 0.5)
        self.ca.assert_that_pv_is(w_pv, -0.5)

