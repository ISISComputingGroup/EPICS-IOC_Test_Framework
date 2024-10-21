import os
import unittest
from collections import OrderedDict

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list

MTR_01 = "GALIL_01"

# PV names for motors
JAWS_BASE_PV = "MOT:JAWS1"
DIRECTIONS = ["N", "S", "E", "W"]

TEST_POSITIONS = [-5, 0, 10, 10e-1]

# Tests will fail if JAWS support module is not up to date and built
test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "jaws", "master", "settings", "jaws_full")
)

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


class JawsTestsBase(object):
    """
    Base class for jaws tests
    """

    def setUp(self):
        self.setup_jaws()
        self._ioc = IOCRegister.get_running("jaws")
        self.ca = ChannelAccess(default_timeout=30)
        for mtr in self.UNDERLYING_MTRS.values():
            self.ca.set_pv_value("{}.DISP".format(mtr), 0)
            self.ca.set_pv_value("{}.VMAX".format(mtr), 100)
            self.ca.set_pv_value("{}.VELO".format(mtr), 100)

        self.ca.set_pv_value("{}:ABLE:SP".format(JAWS_BASE_PV), 0)
        self.ca.set_pv_value("{}:LOCK:SP".format(JAWS_BASE_PV), 0)

        self.ca.set_pv_value("MOT:JAWS1:HGAP:SP", 0)
        self.ca.set_pv_value("MOT:JAWS1:VGAP:SP", 0)
        self.ca.set_pv_value("MOT:JAWS1:HCENT:SP", 0)
        self.ca.set_pv_value("MOT:JAWS1:VCENT:SP", 0)

    @parameterized.expand(parameterized_list(DIRECTIONS))
    def test_GIVEN_ioc_started_THEN_underlying_mtr_fields_can_be_read(self, _, direction):
        underlying_mtr = self.UNDERLYING_MTRS[direction]

        expected = self.ca.get_pv_value("{}.VELO".format(underlying_mtr))
        jaw_blade_pv = "{}:J{}".format(JAWS_BASE_PV, direction)

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

    def test_GIVEN_jaws_closed_at_centre_WHEN_JN_moves_THEN_vcent_moves(self):
        n_pv = "{}:JN".format(JAWS_BASE_PV)
        n_pv_sp = "{}:JN:SP".format(JAWS_BASE_PV)
        s_pv = "{}:JS".format(JAWS_BASE_PV)
        # GIVEN
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0)
        # WHEN
        self.ca.set_pv_value(n_pv_sp, 1)
        # THEN
        self.ca.assert_that_pv_is(n_pv, 1)
        self.ca.assert_that_pv_is(s_pv, 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 1)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP:SP", 1)
        self.ca.assert_that_pv_is("MOT:JAWS1:HGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:HGAP:SP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0.5)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT:SP", 0.5)
        self.ca.assert_that_pv_is(n_pv_sp, 1)

    def test_GIVEN_jaws_closed_at_centre_WHEN_north_low_moved_THEN_vcent_not_move(self):
        testval = 1
        n_pv = "{}:JN".format(JAWS_BASE_PV)
        n_pv_sp = "{}:JN:SP".format(JAWS_BASE_PV)
        n_pv_low_sp = "{}:JN:MTR".format(JAWS_BASE_PV)
        n_pv_low = "{}:JN:MTR.RBV".format(JAWS_BASE_PV)
        s_pv = "{}:JS".format(JAWS_BASE_PV)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0)
        self.ca.assert_that_pv_is(n_pv_low, 0)
        # WHEN
        self.ca.set_pv_value(n_pv_low_sp, testval)
        # THEN
        self.ca.assert_that_pv_is(n_pv_low, testval)
        self.ca.assert_that_pv_is(n_pv, testval)
        self.ca.assert_that_pv_is(n_pv_sp, 0)
        self.ca.assert_that_pv_is(s_pv, 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:HGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:HGAP:SP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", testval / 2.0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT:SP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP:SP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", testval)

    def test_GIVEN_jaws_offset_WHEN_gap_set_THEN_centre_maintained(self):
        n_pv = "{}:JN".format(JAWS_BASE_PV)
        n_pv_sp = "{}:JN:SP".format(JAWS_BASE_PV)
        n_pv_low_sp = "{}:JN:MTR".format(JAWS_BASE_PV)
        n_pv_low = "{}:JN:MTR.RBV".format(JAWS_BASE_PV)
        s_pv = "{}:JS".format(JAWS_BASE_PV)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0)
        self.ca.assert_that_pv_is(n_pv_low, 0)
        # WHEN
        self.ca.set_pv_value(n_pv_low_sp, 1)
        self.ca.assert_that_pv_is(n_pv_low, 1)
        self.ca.assert_that_pv_is(n_pv_sp, 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0.5)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT:SP", 0)
        self.ca.set_pv_value("MOT:JAWS1:VGAP:SP", 4)
        # THEN
        self.ca.assert_that_pv_is(n_pv, 2)
        self.ca.assert_that_pv_is(n_pv_sp, 2)
        self.ca.assert_that_pv_is(s_pv, -2)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 4)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT:SP", 0)

    def test_GIVEN_jaws_offset_WHEN_centre_set_THEN_gap_maintained(self):
        n_pv = "{}:JN".format(JAWS_BASE_PV)
        n_pv_sp = "{}:JN:SP".format(JAWS_BASE_PV)
        n_pv_low_sp = "{}:JN:MTR".format(JAWS_BASE_PV)
        n_pv_low = "{}:JN:MTR.RBV".format(JAWS_BASE_PV)
        s_pv = "{}:JS".format(JAWS_BASE_PV)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0)
        self.ca.assert_that_pv_is(n_pv_low, 0)
        # WHEN
        self.ca.set_pv_value(n_pv_low_sp, 1)
        self.ca.assert_that_pv_is(n_pv_low, 1)
        self.ca.assert_that_pv_is(n_pv_sp, 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 0.5)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT:SP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 1)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP:SP", 0)
        self.ca.set_pv_value("MOT:JAWS1:VCENT:SP", 4)
        # THEN
        self.ca.assert_that_pv_is(n_pv, 4)
        self.ca.assert_that_pv_is(n_pv_sp, 4)
        self.ca.assert_that_pv_is(s_pv, 4)
        self.ca.assert_that_pv_is("MOT:JAWS1:VGAP", 0)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT", 4)
        self.ca.assert_that_pv_is("MOT:JAWS1:VCENT:SP", 4)

    @parameterized.expand([("lock", "Unlocked"), ("able", "Enable")])
    def test_GIVEN_all_jaws_have_state_set_THEN_overall_state_is_set(self, key, expected):
        enabled_val = 0
        for mtr in self.UNDERLYING_MTRS.values():
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv, enabled_val)

        jaws_status_readback_pv = "{}:{}".format(JAWS_BASE_PV, key.upper())
        actual = self.ca.get_pv_value(jaws_status_readback_pv)

        self.assertEqual(expected, actual)

    @parameterized.expand([("lock", "Locked"), ("able", "Disable")])
    def test_GIVEN_no_jaws_have_state_set_THEN_overall_state_is_not_set(self, key, expected):
        disabled_val = 1
        for mtr in self.UNDERLYING_MTRS.values():
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv, disabled_val)

        jaws_status_readback_pv = "{}:{}".format(JAWS_BASE_PV, key.upper())
        actual = self.ca.get_pv_value(jaws_status_readback_pv)

        self.assertEqual(expected, actual)

    @parameterized.expand([("lock", "Unknown"), ("able", "Unknown")])
    def test_GIVEN_some_jaws_have_state_set_THEN_overall_state_is_unknown(self, key, expected):
        disabled_val = 0
        enabled_val = 1
        for mtr in list(self.UNDERLYING_MTRS.values())[:2]:
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv, enabled_val)
        for mtr in list(self.UNDERLYING_MTRS.values())[2:]:
            mtr_status_pv = "{}_{}".format(mtr, key)
            self.ca.set_pv_value(mtr_status_pv, disabled_val)

        jaws_status_readback_pv = "{}:{}".format(JAWS_BASE_PV, key.upper())
        actual = self.ca.get_pv_value(jaws_status_readback_pv)

        self.assertEqual(expected, actual)

    @parameterized.expand(parameterized_list(DIRECTIONS))
    def test_GIVEN_underlying_mtr_adel_value_THEN_jaws_ADEL_field_mirrored(self, _, direction):
        motor_adel_pv = "{}.ADEL".format(self.UNDERLYING_MTRS[direction])
        jaw_adel_pv = "{}:J{}.ADEL".format(JAWS_BASE_PV, direction)

        self.ca.set_pv_value(motor_adel_pv, 0.0)
        self.ca.assert_that_pv_is(motor_adel_pv, 0.0)

        test_values = [1e-4, 1.2, 12.3]

        for test_value in test_values:
            self.ca.set_pv_value(motor_adel_pv, test_value)

            self.ca.assert_that_pv_is_number(motor_adel_pv, test_value)
            self.ca.assert_that_pv_is_number(jaw_adel_pv, test_value)

    @parameterized.expand([("V", "N"), ("H", "E")])
    def test_GIVEN_underlying_mtr_adel_THEN_jaws_centre_and_gap_adel_mirrored(
        self, axis, underlying_mtr_direction
    ):
        underlying_mtr = self.UNDERLYING_MTRS[underlying_mtr_direction]
        motor_pv = "{}.ADEL".format(underlying_mtr)

        test_values = [1e-4, 1.2, 12.3]
        for test_value in test_values:
            self.ca.set_pv_value(motor_pv, test_value)

            self.ca.assert_that_pv_is_number(motor_pv, test_value)

            self.ca.assert_that_pv_is_number(
                "{}:{}CENT.ADEL".format(JAWS_BASE_PV, axis), test_value
            )
            self.ca.assert_that_pv_is_number("{}:{}GAP.ADEL".format(JAWS_BASE_PV, axis), test_value)


class JawsTests(JawsTestsBase, unittest.TestCase):
    """
    Tests for vertical jaws
    """

    def setup_jaws(self):
        self.MTR_NORTH = "MOT:MTR0101"
        self.MTR_SOUTH = "MOT:MTR0102"
        self.MTR_WEST = "MOT:MTR0103"
        self.MTR_EAST = "MOT:MTR0104"
        self.UNDERLYING_MTRS = OrderedDict(
            [
                ("N", self.MTR_NORTH),
                ("S", self.MTR_SOUTH),
                ("E", self.MTR_EAST),
                ("W", self.MTR_WEST),
            ]
        )
