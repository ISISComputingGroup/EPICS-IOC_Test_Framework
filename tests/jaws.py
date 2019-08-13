import unittest
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list
from parameterized import parameterized

MTR_01 = "GALIL_01"

# PV names for motors
JAWS_BASE_PV = "MOT:JAWS1"
DIRECTIONS = ["N", "S", "E", "W"]

TEST_POSITIONS = [-5, 0, 10, 10e-1]

# Tests will fail if JAWS support module is not up to date and built
test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "jaws", "master", "settings", "jaws_full"))

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
]

TEST_MODES = [TestModes.DEVSIM]


class JawsTests(unittest.TestCase):

    """
    Tests for vertical jaws
    """
    MTR_NORTH = "MOT:MTR0101"
    MTR_SOUTH = "MOT:MTR0102"
    MTR_EAST = "MOT:MTR0103"
    MTR_WEST = "MOT:MTR0104"
    UNDERLYING_MTRS = [MTR_NORTH, MTR_SOUTH, MTR_EAST, MTR_WEST]

    def setUp(self):
        self._ioc = IOCRegister.get_running("jaws")
        self.ca = ChannelAccess(default_timeout=30)
        for mtr in self.UNDERLYING_MTRS:
            self.ca.set_pv_value("{}.VMAX".format(mtr), 100)
            self.ca.set_pv_value("{}.VELO".format(mtr), 100)

        self.ca.set_pv_value("{}:ABLE:SP".format(JAWS_BASE_PV), 0)
        self.ca.set_pv_value("{}:LOCK:SP".format(JAWS_BASE_PV), 0)

        self.ca.set_pv_value("MOT:JAWS1:HGAP:SP", 0)
        self.ca.set_pv_value("MOT:JAWS1:VGAP:SP", 0)

    def test_GIVEN_ioc_started_THEN_underlying_mtr_north_fields_can_be_read(self):
        underlying_mtr = self.MTR_NORTH
        direction_key = "JN"

        expected = self.ca.get_pv_value("{}.VELO".format(underlying_mtr))
        jaw_blade_pv = "{}:{}".format(JAWS_BASE_PV, direction_key)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(jaw_blade_pv))

        self.assertEqual(expected, actual)

    def test_GIVEN_ioc_started_THEN_underlying_mtr_south_fields_can_be_read(self):
        underlying_mtr = self.MTR_SOUTH
        direction_key = "JS"

        expected = self.ca.get_pv_value("{}.VELO".format(underlying_mtr))
        jaw_blade_pv = "{}:{}".format(JAWS_BASE_PV, direction_key)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(jaw_blade_pv))

        self.assertEqual(expected, actual)

    def test_GIVEN_ioc_started_THEN_underlying_mtr_east_fields_can_be_read(self):
        underlying_mtr = self.MTR_EAST
        direction_key = "JE"

        expected = self.ca.get_pv_value("{}.VELO".format(underlying_mtr))
        jaw_blade_pv = "{}:{}".format(JAWS_BASE_PV, direction_key)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(jaw_blade_pv))

        self.assertEqual(expected, actual)

    def test_GIVEN_ioc_started_THEN_underlying_mtr_west_fields_can_be_read(self):
        underlying_mtr = self.MTR_WEST
        direction_key = "JW"

        expected = self.ca.get_pv_value("{}.VELO".format(underlying_mtr))
        jaw_blade_pv = "{}:{}".format(JAWS_BASE_PV, direction_key)

        actual = self.ca.get_pv_value("{}:MTR.VELO".format(jaw_blade_pv))

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


    @parameterized.expand([("lock", "Unlocked"),
                           ("able", "Enable")])
    def test_GIVEN_all_jaws_have_state_set_THEN_overall_state_is_set(self, key, expected):
        enabled_val = 0
        for mtr in self.UNDERLYING_MTRS:
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv.format(JAWS_BASE_PV), enabled_val)

        jaws_status_readback_pv = "{}:{}".format(JAWS_BASE_PV, key.upper())
        actual = self.ca.get_pv_value(jaws_status_readback_pv)

        self.assertEqual(expected, actual)

    @parameterized.expand([("lock", "Locked"),
                           ("able", "Disable")])
    def test_GIVEN_no_jaws_have_state_set_THEN_overall_state_is_not_set(self, key, expected):
        disabled_val = 1
        for mtr in self.UNDERLYING_MTRS:
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv.format(JAWS_BASE_PV), disabled_val)

        jaws_status_readback_pv = "{}:{}".format(JAWS_BASE_PV, key.upper())
        actual = self.ca.get_pv_value(jaws_status_readback_pv)

        self.assertEqual(expected, actual)

    @parameterized.expand([("lock", "Unknown"),
                           ("able", "Unknown")])
    def test_GIVEN_some_jaws_have_state_set_THEN_overall_state_is_unknown(self, key, expected):
        disabled_val = 0
        enabled_val = 1
        for mtr in self.UNDERLYING_MTRS[:2]:
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv.format(JAWS_BASE_PV), enabled_val)
        for mtr in self.UNDERLYING_MTRS[2:]:
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv.format(JAWS_BASE_PV), disabled_val)

        jaws_status_readback_pv = "{}:{}".format(JAWS_BASE_PV, key.upper())
        actual = self.ca.get_pv_value(jaws_status_readback_pv)

        self.assertEqual(expected, actual)
