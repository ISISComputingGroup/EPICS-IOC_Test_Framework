import unittest
from unittest import skipIf

import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

GALIL_ADDR = "128.0.0.0"

test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motionSetPoints", "master", "settings", "system_tests"))

# Create 2 Galils
IOCS = [{
            "name": "GALIL_0{}".format(i),
            "directory": get_default_ioc_dir("GALIL", i),
            "custom_prefix": "MOT",
            "pv_for_existence": "MTR0{}01".format(i),
            "macros": {
                "GALILADDR": GALIL_ADDR,
                "MTRCTRL": "0{}".format(i),
                "GALILCONFIGDIR": test_path.replace("\\", "/"),
            }
           } for i in range(1, 3)]

TEST_MODES = [TestModes.RECSIM]

# Device prefix
DEVICE_PREFIX_1D = "LKUP:1DAXIS"
DEVICE_PREFIX_2D = "LKUP:2DAXIS"
DEVICE_PREFIX_10D = "LKUP:10DAXIS"
DEVICE_PREFIX_DN = "LKUP:DN"
DEVICE_PREFIX_DP = "LKUP:DP"

MOTOR_PREFIX = "MOT"

POSITION_IN = "In"
POSITION_OUT = "Out"
MOTOR_POSITION_IN = 3
MOTOR_POSITION_OUT = 1
POSITIONS_1D = [(POSITION_IN, MOTOR_POSITION_IN),
                (POSITION_OUT, MOTOR_POSITION_OUT)]

POSITION_SAMPLE1 = "Sample1"
POSITION_SAMPLE2 = "Sample2"
MOTOR_POSITION_SAMPLE1_COORD0 = 3
MOTOR_POSITION_SAMPLE1_COORD1 = -2
MOTOR_POSITION_SAMPLE2_COORD0 = 1
MOTOR_POSITION_SAMPLE2_COORD1 = -3
POSITIONS_2D = [
    (POSITION_SAMPLE1, MOTOR_POSITION_SAMPLE1_COORD0, MOTOR_POSITION_SAMPLE1_COORD1),
    (POSITION_SAMPLE2, MOTOR_POSITION_SAMPLE2_COORD0, MOTOR_POSITION_SAMPLE2_COORD1),
    ("Sample3", 0, -4),
    ("Sample4", 1, -4)
]


def assert_alarm_state_of_posn(channel_access, coordinate, expected_state):
    channel_access.assert_that_pv_alarm_is("FORWARD_ALARM", expected_state)
    channel_access.assert_that_pv_alarm_is("POSN", expected_state)
    channel_access.assert_that_pv_alarm_is("POSITIONED", expected_state)
    channel_access.assert_that_pv_alarm_is("POSN_NO_ERR", ChannelAccess.Alarms.NONE)


class MotionSetpointsTests(unittest.TestCase):
    """
    Tests the motion setpoints.
    """

    def setUp(self):
        self.ca1D = ChannelAccess(device_prefix=DEVICE_PREFIX_1D)
        self.ca2D = ChannelAccess(device_prefix=DEVICE_PREFIX_2D)
        self.ca10D = ChannelAccess(device_prefix=DEVICE_PREFIX_10D)
        self.caDN = ChannelAccess(device_prefix=DEVICE_PREFIX_DN)
        self.caDP = ChannelAccess(device_prefix=DEVICE_PREFIX_DP)
        self.motor_ca = ChannelAccess(device_prefix=MOTOR_PREFIX)

        self.motor_ca.set_pv_value("MTR0101.HLM", 30)
        self.motor_ca.set_pv_value("MTR0102.HLM", 30)

        self.ca1D.set_pv_value("COORD0:OFFSET:SP", 0)
        self.ca1D.assert_that_pv_is("STATIONARY0", 1, timeout=10)

        self.ca2D.set_pv_value("COORD0:OFFSET:SP", 0)
        self.ca2D.set_pv_value("COORD1:OFFSET:SP", 0)
        self.ca2D.assert_that_pv_is("STATIONARY0", 1, timeout=10)
        self.ca2D.assert_that_pv_is("STATIONARY1", 1, timeout=10)

        for axis in range(1, 9):
            self.motor_ca.set_pv_value("MTR010{}.VMAX".format(axis), 1)
            self.motor_ca.set_pv_value("MTR010{}.VELO".format(axis), 1)
            self.motor_ca.set_pv_value("MTR020{}.VMAX".format(axis), 1)
            self.motor_ca.set_pv_value("MTR020{}.VELO".format(axis), 1)

    def test_GIVEN_1D_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position) in enumerate(POSITIONS_1D):

            self.ca1D.set_pv_value("POSN:SP", expected_position)

            self.ca1D.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca1D.assert_that_pv_is("IPOSN:SP:RBV", index)
            self.motor_ca.assert_that_pv_is("MTR0101.RBV", expected_motor_position)
            self.ca1D.assert_that_pv_is("POSN", expected_position)
            self.ca1D.assert_that_pv_alarm_is("POSN", ChannelAccess.Alarms.NONE)
            self.ca1D.assert_that_pv_is("IPOSN", index)

    def test_GIVEN_1D_WHEN_set_position_by_index_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position) in enumerate(POSITIONS_1D):

            self.ca1D.set_pv_value("IPOSN:SP", index)

            self.ca1D.assert_that_pv_is("IPOSN", index)
            self.ca1D.assert_that_pv_is("POSN", expected_position)
            self.motor_ca.assert_that_pv_is("MTR0101.RBV", expected_motor_position)

    def test_GIVEN_1D_WHEN_move_to_out_position_THEN_in_position_light_goes_off_then_on(self):
        self.ca1D.set_pv_value("POSN:SP", POSITION_IN)
        self.ca1D.assert_that_pv_is("POSN", POSITION_IN)
        self.ca1D.set_pv_value("POSN:SP", POSITION_OUT)

        self.ca1D.assert_that_pv_is("POSITIONED", 0)
        self.ca1D.assert_that_pv_is("STATIONARY0", 0)

        self.ca1D.assert_that_pv_is("POSITIONED", 1)
        self.ca1D.assert_that_pv_is("STATIONARY0", 1)

    def test_GIVEN_1D_WHEN_set_offset_THEN_in_position_light_goes_off_then_on_and_motor_moves_to_position_plus_offset(self):
        expected_offset = 1
        expected_motor_position = MOTOR_POSITION_IN + expected_offset
        self.ca1D.set_pv_value("POSN:SP", POSITION_IN)
        self.ca1D.assert_that_pv_is("POSN", POSITION_IN)
        self.ca1D.assert_that_pv_is("POSITIONED", 1)

        self.ca1D.set_pv_value("COORD0:OFFSET:SP", expected_offset)
        self.ca1D.assert_that_pv_is("POSITIONED", 0)

        self.ca1D.assert_that_pv_is("POSITIONED", 1)
        self.ca1D.assert_that_pv_is("COORD0:OFFSET", expected_offset)
        self.motor_ca.assert_that_pv_is("MTR0101.RBV", expected_motor_position)

    def test_GIVEN_1D_WHEN_set_large_offset_THEN_current_position_set_correctly(self):
        offset = MOTOR_POSITION_OUT - MOTOR_POSITION_IN
        self.ca1D.set_pv_value("COORD0:OFFSET:SP", -offset)

        self.ca1D.set_pv_value("POSN:SP", POSITION_OUT)

        self.ca1D.assert_that_pv_is("POSITIONED", 0)
        self.ca1D.assert_that_pv_is("POSITIONED", 1)
        self.ca1D.assert_that_pv_is("POSN", POSITION_OUT, timeout=30)

    def test_GIVEN_1D_WHEN_get_numaxes_THEN_return1(self):
        self.ca1D.assert_that_pv_is("NUMAXES", 1)

    def test_GIVEN_2D_WHEN_get_numaxes_THEN_return2(self):
        self.ca2D.assert_that_pv_is("NUMAXES", 2)

    def test_GIVEN_2D_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position_cord1, expected_motor_position_cord2) in \
                enumerate(POSITIONS_2D):

            self.ca2D.set_pv_value("POSN:SP", expected_position)

            self.ca2D.assert_that_pv_is("POSN", expected_position)
            self.ca2D.assert_that_pv_alarm_is("POSN", ChannelAccess.Alarms.NONE)
            self.ca2D.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca2D.assert_that_pv_is("IPOSN", index)
            self.motor_ca.assert_that_pv_is("MTR0101.RBV", expected_motor_position_cord1)
            self.motor_ca.assert_that_pv_is("MTR0102.RBV", expected_motor_position_cord2)

    def test_GIVEN_2D_WHEN_move_to_out_position_THEN_in_position_light_goes_off_then_on(self):
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE2)

        self.ca2D.assert_that_pv_is("POSITIONED", 0)
        self.ca2D.assert_that_pv_is("STATIONARY0", 0)

        self.ca2D.assert_that_pv_is("POSITIONED", 1)
        self.ca2D.assert_that_pv_is("STATIONARY0", 1)

    def test_GIVEN_2D_WHEN_set_offset_THEN_in_position_light_goes_off_then_on_and_motor_moves_to_position_plus_offset(self):
        expected_offset_COORD0 = 1
        expected_motor_position_COORD0 = MOTOR_POSITION_SAMPLE1_COORD0 + expected_offset_COORD0
        expected_offset_COORD1 = 2
        expected_motor_position_COORD1 = MOTOR_POSITION_SAMPLE1_COORD1 + expected_offset_COORD1
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSITIONED", 1)

        self.ca2D.set_pv_value("COORD0:OFFSET:SP", expected_offset_COORD0)
        self.ca2D.set_pv_value("COORD1:OFFSET:SP", expected_offset_COORD1)
        self.ca2D.assert_that_pv_is("POSITIONED", 0)

        self.ca2D.assert_that_pv_is("POSITIONED", 1)
        self.ca2D.assert_that_pv_is("COORD0:OFFSET", expected_offset_COORD0)
        self.ca2D.assert_that_pv_is("COORD1:OFFSET", expected_offset_COORD1)
        self.motor_ca.assert_that_pv_is("MTR0101.RBV", expected_motor_position_COORD0)
        self.motor_ca.assert_that_pv_is("MTR0102.RBV", expected_motor_position_COORD1)

    def test_GIVEN_2D_WHEN_set_large_offset_THEN_current_position_is_correct(self):
        """
        Originally the offset was included in the value sent to lookup so if the offset was large compared with
        differences between samples it set the wrong value.
        """
        offset_COORD0 = MOTOR_POSITION_SAMPLE1_COORD0 - MOTOR_POSITION_SAMPLE2_COORD0
        offset_COORD1 = MOTOR_POSITION_SAMPLE1_COORD1 - MOTOR_POSITION_SAMPLE2_COORD1

        self.ca2D.set_pv_value("COORD0:OFFSET:SP", -offset_COORD0)
        self.ca2D.set_pv_value("COORD1:OFFSET:SP", -offset_COORD1)
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)

        self.ca2D.assert_that_pv_is("POSITIONED", 0)
        self.ca2D.assert_that_pv_is("POSITIONED", 1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)

    def test_GIVEN_file_WHEN_duplicate_name_value_THEN_load_no_positions(self):
        self.caDN.assert_that_pv_is("POSN:NUM", 0)

    def test_GIVEN_file_WHEN_duplicate_position_value_THEN_load_no_positions(self):
        self.caDP.assert_that_pv_is("POSN:NUM", 0)

    def test_GIVEN_2D_WHEN_invalid_position_specified_THEN_alarm(self):
        self.ca2D.set_pv_value("POSN:SP", "an_invalid_position")
        self.ca2D.assert_that_pv_alarm_is("POSN:SP", ChannelAccess.Alarms.INVALID)

    def test_GIVEN_2D_WHEN_move_motor_THEN_tolerance_checked(self):
        self.ca2D.set_pv_value("TOLERENCE", 10)
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE2)
        self.motor_ca.assert_that_pv_is("MTR0101.RBV", MOTOR_POSITION_SAMPLE2_COORD0)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE2)
        self.ca2D.assert_that_pv_is("IPOSN", 1)
        """move motor, all should still be OK as within tolerance"""
        self.motor_ca.set_pv_value("MTR0101", MOTOR_POSITION_SAMPLE2_COORD0 - 0.2)
        self.motor_ca.assert_that_pv_is("MTR0101.RBV", MOTOR_POSITION_SAMPLE2_COORD0 - 0.2)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE2)
        self.ca2D.assert_that_pv_is("IPOSN", 1)
        self.ca2D.assert_that_pv_is("POSITIONED", 1)
        """change tolerance, should not be in position"""
        self.ca2D.set_pv_value("TOLERENCE", 0.1)
        self.ca2D.assert_that_pv_is("POSN", "")
        self.ca2D.assert_that_pv_is("IPOSN", -1)
        self.ca2D.assert_that_pv_is("POSITIONED", 0)
        """move motor back, should now be in position again"""
        self.motor_ca.set_pv_value("MTR0101", MOTOR_POSITION_SAMPLE2_COORD0)
        self.motor_ca.assert_that_pv_is("MTR0101.RBV", MOTOR_POSITION_SAMPLE2_COORD0)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE2)
        self.ca2D.assert_that_pv_is("IPOSN", 1)
        self.ca2D.assert_that_pv_is("POSITIONED", 1)

    def _test_alarm_propogates(self, channel_access, motor_num):
        assert_alarm_state_of_posn(channel_access, motor_num, ChannelAccess.Alarms.NONE)

        self.motor_ca.set_pv_value("MTR010{}.HLSV".format(motor_num), "MAJOR")
        current_posn = self.motor_ca.get_pv_value("MTR010{}".format(motor_num))
        self.motor_ca.set_pv_value("MTR010{}.HLM".format(motor_num), current_posn - 1)
        self.motor_ca.assert_that_pv_alarm_is("MTR010{}".format(motor_num), ChannelAccess.Alarms.MAJOR)

        assert_alarm_state_of_posn(channel_access, motor_num, ChannelAccess.Alarms.MAJOR)

    def test_GIVEN_1D_WHEN_axis_in_alarm_THEN_position_in_alarm(self):
        self._test_alarm_propogates(self.ca1D, 1)

    def test_GIVEN_2D_WHEN_second_axis_in_alarm_THEN_position_in_alarm(self):
        self._test_alarm_propogates(self.ca2D, 2)

    def test_GIVEN_10D_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        def check_motor_positions(expected_coords, readback):
            pv_suffix = ".RBV" if readback else ""
            for index, coord in enumerate(expected_coords):
                controller = 1 if index < 8 else 2
                axis = (index % 8) + 1
                self.motor_ca.assert_that_pv_is_number("MTR0{}0{}{}".format(controller, axis, pv_suffix), coord, 0.1)

        for sample_num in range(2):
            sample_name = "Sample{}".format(sample_num + 1)
            self.ca10D.set_pv_value("POSN:SP", sample_name)

            expected_coords = [i + sample_num * 5 for i in range(1, 11)]
            check_motor_positions(expected_coords, False)
            check_motor_positions(expected_coords, True)

            self.ca10D.assert_that_pv_is("POSN", sample_name)
            self.ca10D.assert_that_pv_alarm_is("POSN", ChannelAccess.Alarms.NONE)
            self.ca10D.assert_that_pv_is("POSN:SP:RBV", sample_name)
            self.ca10D.assert_that_pv_is("IPOSN", sample_num)

