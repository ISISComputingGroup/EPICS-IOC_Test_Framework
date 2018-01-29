import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# Internal Address of device (must be 2 characters)
ADDRESS = "01"

# MACROS to use for the IOC
MACROS = {"ADDR": ADDRESS}

# Device prefix
DEVICE_PREFIX_1D_NO_AXIS = "LKUP:1D"
DEVICE_PREFIX_2D_NO_AXIS = "LKUP:2D"
DEVICE_PREFIX_1D_WITH_AXIS = "LKUP:1DAXIS"
DEVICE_PREFIX_2D_WITH_AXIS = "LKUP:2DAXIS"

MOTOR_PREFIX = "MSP"

POSITION_IN = "In"
POSITION_OUT = "Out"
MOTOR_POSITION_IN = 3
MOTOR_POSITION_OUT = 1
POSITIONS_1D = [(POSITION_IN, MOTOR_POSITION_IN),
                (POSITION_OUT, MOTOR_POSITION_OUT)]

POSITION_SAMPLE1 = "Sample1"
POSITION_SAMPLE2 = "Sample2"
MOTOR_POSITION_SAMPLE1_COORD1 = 3
MOTOR_POSITION_SAMPLE1_COORD2 = -2
MOTOR_POSITION_SAMPLE2_COORD1 = 1
MOTOR_POSITION_SAMPLE2_COORD2 = -3
POSITIONS_2D = [
    (POSITION_SAMPLE1, MOTOR_POSITION_SAMPLE1_COORD1, MOTOR_POSITION_SAMPLE1_COORD2),
    (POSITION_SAMPLE2, MOTOR_POSITION_SAMPLE2_COORD1, MOTOR_POSITION_SAMPLE2_COORD2),
    ("Sample3", 0, -4)
]


class Motion_setpointsTests(unittest.TestCase):
    """
    Tests the motion setpoints.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("motion_setpoints")

        self.ca1D = ChannelAccess(device_prefix=DEVICE_PREFIX_1D_NO_AXIS)
        self.ca2D = ChannelAccess(device_prefix=DEVICE_PREFIX_2D_NO_AXIS)
        self.ca1DAxis = ChannelAccess(device_prefix=DEVICE_PREFIX_1D_WITH_AXIS)
        self.ca2DAxis = ChannelAccess(device_prefix=DEVICE_PREFIX_2D_WITH_AXIS)
        self.motor_ca = ChannelAccess(device_prefix=MOTOR_PREFIX)
        self.ca1D.wait_for("COORD1:NAME", timeout=30)
        self.ca1D.set_pv_value("COORD1:OFFSET:SP", 0)
        self.ca1D.assert_that_pv_is("STATIONARY", 1)

        self.ca2D.set_pv_value("COORD1:OFFSET:SP", 0)
        self.ca2D.set_pv_value("COORD2:OFFSET:SP", 0)
        self.ca2D.assert_that_pv_is("STATIONARY", 1)
        self.ca2D.assert_that_pv_is("STATIONARY2", 1)

        self.ca1DAxis.set_pv_value("COORD1:OFFSET:SP", 0)
        self.ca1DAxis.assert_that_pv_is("STATIONARY", 1)

        self.ca2DAxis.set_pv_value("COORD1:OFFSET:SP", 0)
        self.ca2DAxis.set_pv_value("COORD1:OFFSET:SP", 0)
        self.ca2DAxis.assert_that_pv_is("STATIONARY", 1)
        self.ca2DAxis.assert_that_pv_is("STATIONARY2", 1)

    def test_GIVEN_1D_no_axis_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position) in enumerate(POSITIONS_1D):

            self.ca1D.set_pv_value("POSN:SP", expected_position)

            self.ca1D.assert_that_pv_is("POSN", expected_position)
            self.ca1D.assert_pv_alarm_is("POSN", ChannelAccess.ALARM_NONE)
            self.ca1D.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca1D.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca1D.assert_that_pv_is("IPOSN", index)
            self.motor_ca.assert_that_pv_is("MTR0.RBV", expected_motor_position)
            self.ca1D.assert_that_pv_is("COORD1:MTR.RBV", expected_motor_position)

    def test_GIVEN_1D_no_axis_WHEN_set_position_by_index_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position) in enumerate(POSITIONS_1D):

            self.ca1D.set_pv_value("IPOSN:SP", index)

            self.ca1D.assert_that_pv_is("IPOSN", index)
            self.ca1D.assert_that_pv_is("POSN", expected_position)
            self.motor_ca.assert_that_pv_is("MTR0.RBV", expected_motor_position)

    def test_GIVEN_1D_WHEN_move_to_out_position_THEN_in_position_light_goes_off_then_on(self):
        self.ca1D.set_pv_value("POSN:SP", POSITION_IN)
        self.ca1D.assert_that_pv_is("POSN", POSITION_IN)
        self.ca1D.set_pv_value("POSN:SP", POSITION_OUT)

        self.ca1D.assert_that_pv_is("POSITIONED", 0)
        self.ca1D.assert_that_pv_is("STATIONARY", 0)

        self.ca1D.assert_that_pv_is("POSITIONED", 1)
        self.ca1D.assert_that_pv_is("STATIONARY", 1)

    def test_GIVEN_1D_WHEN_set_offset_THEN_in_position_light_goes_off_then_on_and_motor_moves_to_position_plus_offset(self):
        expected_offset = 1
        expected_motor_position = MOTOR_POSITION_IN + expected_offset
        self.ca1D.set_pv_value("POSN:SP", POSITION_IN)
        self.ca1D.assert_that_pv_is("POSN", POSITION_IN)
        self.ca1D.assert_that_pv_is("POSITIONED", 1)

        self.ca1D.set_pv_value("COORD1:OFFSET:SP", expected_offset)
        self.ca1D.assert_that_pv_is("POSITIONED", 0)

        self.ca1D.assert_that_pv_is("POSITIONED", 1)
        self.ca1D.assert_that_pv_is("COORD1:OFFSET", expected_offset)
        self.motor_ca.assert_that_pv_is("MTR0.RBV", expected_motor_position)

    def test_GIVEN_1D_WHEN_set_large_offset_THEN_current_position_set_correctly(self):
        offset = MOTOR_POSITION_OUT - MOTOR_POSITION_IN
        self.ca1D.set_pv_value("COORD1:OFFSET:SP", -offset)

        self.ca1D.set_pv_value("POSN:SP", POSITION_OUT)

        self.ca1D.assert_that_pv_is("POSITIONED", 0)
        self.ca1D.assert_that_pv_is("POSITIONED", 1)
        self.ca1D.assert_that_pv_is("POSN", POSITION_OUT, timeout=30)


    def test_GIVEN_1D_no_axis_WHEN_get_numaxes_THEN_return1(self):
        self.ca1D.assert_that_pv_is("NUMAXES", 1)

    def test_GIVEN_2D_no_axis_WHEN_get_numaxes_THEN_return2(self):
        self.ca2D.assert_that_pv_is("NUMAXES", 2)

    def test_GIVEN_2D_no_axis_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position_cord1, expected_motor_position_cord2) in \
                enumerate(POSITIONS_2D):

            self.ca2D.set_pv_value("POSN:SP", expected_position)

            self.ca2D.assert_that_pv_is("POSN", expected_position)
            self.ca2D.assert_pv_alarm_is("POSN", ChannelAccess.ALARM_NONE)
            self.ca2D.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca2D.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca2D.assert_that_pv_is("IPOSN", index)
            self.motor_ca.assert_that_pv_is("MTR0.RBV", expected_motor_position_cord1)
            self.motor_ca.assert_that_pv_is("MTR1.RBV", expected_motor_position_cord2)
            self.ca2D.assert_that_pv_is("COORD1:MTR.RBV", expected_motor_position_cord1)
            self.ca2D.assert_that_pv_is("COORD2:MTR.RBV", expected_motor_position_cord2)

    def test_GIVEN_2D_WHEN_move_to_out_position_THEN_in_position_light_goes_off_then_on(self):
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE2)

        self.ca2D.assert_that_pv_is("POSITIONED", 0)
        self.ca2D.assert_that_pv_is("STATIONARY", 0)

        self.ca2D.assert_that_pv_is("POSITIONED", 1)
        self.ca2D.assert_that_pv_is("STATIONARY", 1)

    def test_GIVEN_2D_WHEN_set_offset_THEN_in_position_light_goes_off_then_on_and_motor_moves_to_position_plus_offset(self):
        expected_offset_coord1 = 1
        expected_motor_position_coord1 = MOTOR_POSITION_SAMPLE1_COORD1 + expected_offset_coord1
        expected_offset_coord2 = 2
        expected_motor_position_coord2 = MOTOR_POSITION_SAMPLE1_COORD2 + expected_offset_coord2
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSITIONED", 1)

        self.ca2D.set_pv_value("COORD1:OFFSET:SP", expected_offset_coord1)
        self.ca2D.set_pv_value("COORD2:OFFSET:SP", expected_offset_coord2)
        self.ca2D.assert_that_pv_is("POSITIONED", 0)

        self.ca2D.assert_that_pv_is("POSITIONED", 1)
        self.ca2D.assert_that_pv_is("COORD1:OFFSET", expected_offset_coord1)
        self.ca2D.assert_that_pv_is("COORD2:OFFSET", expected_offset_coord2)
        self.motor_ca.assert_that_pv_is("MTR0.RBV", expected_motor_position_coord1)
        self.motor_ca.assert_that_pv_is("MTR1.RBV", expected_motor_position_coord2)

    def test_GIVEN_2D_WHEN_set_large_offset_THEN_current_position_is_correct(self):
        """
        Originally the offset was included in the value sent to lookup so if the offset was large compared with
        differences between samples it set the wrong value.
        """
        offset_coord1 = MOTOR_POSITION_SAMPLE1_COORD1 - MOTOR_POSITION_SAMPLE2_COORD1
        offset_coord2 = MOTOR_POSITION_SAMPLE1_COORD2 - MOTOR_POSITION_SAMPLE2_COORD2

        self.ca2D.set_pv_value("COORD1:OFFSET:SP", -offset_coord1)
        self.ca2D.set_pv_value("COORD2:OFFSET:SP", -offset_coord2)
        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)

        self.ca2D.assert_that_pv_is("POSITIONED", 0)
        self.ca2D.assert_that_pv_is("POSITIONED", 1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)

    def test_GIVEN_1D_with_axis_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position) in enumerate(POSITIONS_1D):

            self.ca1DAxis.set_pv_value("POSN:SP", expected_position)

            self.ca1DAxis.assert_that_pv_is("POSN", expected_position)
            self.ca1DAxis.assert_pv_alarm_is("POSN", ChannelAccess.ALARM_NONE)
            self.ca1DAxis.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca1DAxis.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca1DAxis.assert_that_pv_is("IPOSN", index)
            self.motor_ca.assert_that_pv_is("MTR0.RBV", expected_motor_position)
            self.ca1DAxis.assert_that_pv_is("COORD1:MTR.RBV", expected_motor_position)

    def test_GIVEN_2D_with_axis_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position_cord1, expected_motor_position_cord2) in \
                enumerate(POSITIONS_2D):

            self.ca2DAxis.set_pv_value("POSN:SP", expected_position)

            self.ca2DAxis.assert_that_pv_is("POSN", expected_position)
            self.ca2DAxis.assert_pv_alarm_is("POSN", ChannelAccess.ALARM_NONE)
            self.ca2DAxis.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca2DAxis.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca2DAxis.assert_that_pv_is("IPOSN", index)
            self.ca2DAxis.assert_that_pv_is("COORD1:MTR.RBV", expected_motor_position_cord1)
            self.ca2DAxis.assert_that_pv_is("COORD2:MTR.RBV", expected_motor_position_cord2)
            self.motor_ca.assert_that_pv_is("MTR0.RBV", expected_motor_position_cord1)
            self.motor_ca.assert_that_pv_is("MTR1.RBV", expected_motor_position_cord2)
