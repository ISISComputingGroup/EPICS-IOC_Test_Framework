import unittest
from parameterized import parameterized
from operator import add
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list

GALIL_ADDR = "127.0.0.11"

test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motionSetPoints", "master", "settings"))

GALIL_AXES_PER_CONTROLLER = 8

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
           } for i in [1, 2]]

TEST_MODES = [TestModes.RECSIM]

# Device prefix
DEVICE_PREFIX_1D = "LKUP1D"
DEVICE_PREFIX_2D = "LKUP2D"
DEVICE_PREFIX_10D = "LKUP10D"
DEVICE_PREFIX_DN = "LKUPDN"
DEVICE_PREFIX_DP = "LKUPDP"

MOTOR_PREFIX = "MOT"

## where "Dup" is added to a position name, this is to create a
## new position with coordinates that is a duplicate of an existing position
## and thus check this is handled correctly during testing

## data below must match test data defined in files in `test_path`  

POSITION_IN = "In"
POSITION_OUT = "Out"
MOTOR_POSITION_IN = 3
MOTOR_POSITION_OUT = 1
POSITIONS_1D = [(POSITION_IN, MOTOR_POSITION_IN),
                (POSITION_IN+"Dup", MOTOR_POSITION_IN),
                (POSITION_OUT+"Dup", MOTOR_POSITION_OUT),
                (POSITION_OUT, MOTOR_POSITION_OUT)]

POSITION_SAMPLE1 = "Sample1"
POSITION_SAMPLE2 = "Sample2"
MOTOR_POSITION_SAMPLE1_COORD0 = 3
MOTOR_POSITION_SAMPLE1_COORD1 = -2
MOTOR_POSITION_SAMPLE2_COORD0 = 1
MOTOR_POSITION_SAMPLE2_COORD1 = 0
POSITIONS_2D = [
    (POSITION_SAMPLE1, MOTOR_POSITION_SAMPLE1_COORD0, MOTOR_POSITION_SAMPLE1_COORD1),
    (POSITION_SAMPLE2+"Dup1", MOTOR_POSITION_SAMPLE2_COORD0, MOTOR_POSITION_SAMPLE2_COORD1),
    (POSITION_SAMPLE2, MOTOR_POSITION_SAMPLE2_COORD0, MOTOR_POSITION_SAMPLE2_COORD1),
    (POSITION_SAMPLE2+"Dup2", MOTOR_POSITION_SAMPLE2_COORD0, MOTOR_POSITION_SAMPLE2_COORD1),
    ("Sample3", 0, -4),
    ("Sample4", 1, -4)
]

POSITIONS_10D = [("Sample1", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                 ("Sample2", 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
                 ("Sample2Dup1", 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
                 ("Sample3", 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)]
POSITION_TABLES = {1: POSITIONS_1D, 2: POSITIONS_2D, 10: POSITIONS_10D}


def assert_alarm_state_of_posn(channel_access, expected_state):
    channel_access.assert_that_pv_alarm_is("FORWARD_ALARM", expected_state)
    channel_access.assert_that_pv_alarm_is("POSN", expected_state)
    channel_access.assert_that_pv_alarm_is("POSITIONED", expected_state)
    channel_access.assert_that_pv_alarm_is("POSN_NO_ERR", ChannelAccess.Alarms.NONE)


def get_motor_pv_from_axis_num(axis_num):
    controller = 1 if axis_num < GALIL_AXES_PER_CONTROLLER else 2
    axis_num = (axis_num % GALIL_AXES_PER_CONTROLLER) + 1
    return "MTR0{}0{}".format(controller, axis_num)


def modify_file_and_assert_test(channel_access, lookup_file, old_text, new_text, test):
    """Modifies lookup_file by replacing any instances of old_text with new_text, calls the supplied test and
    then reverts the file to it's original state.
    """
    with open(lookup_file, "r+") as f:
        original_lookup_text = f.read()
        f.seek(0)
        f.write(original_lookup_text.replace(str(old_text), str(new_text)))

    try:
        channel_access.set_pv_value("RESET", 1)
        test()
    finally:
        with open(lookup_file, "w") as f:
            f.write(original_lookup_text)


class MotionSetpointsTests(unittest.TestCase):
    """
    Tests the motion setpoints.
    """

    @classmethod
    def setUpClass(cls):
        cls.ca1D = ChannelAccess(device_prefix=DEVICE_PREFIX_1D)
        cls.ca2D = ChannelAccess(device_prefix=DEVICE_PREFIX_2D)
        cls.ca10D = ChannelAccess(device_prefix=DEVICE_PREFIX_10D)
        cls.caDN = ChannelAccess(device_prefix=DEVICE_PREFIX_DN)
        cls.caDP = ChannelAccess(device_prefix=DEVICE_PREFIX_DP)
        cls.motor_ca = ChannelAccess(device_prefix=MOTOR_PREFIX)

        cls.channel_access_instances = {1: cls.ca1D, 2: cls.ca2D, 10: cls.ca10D}

        for axis in range(1, 9):
            cls.motor_ca.set_pv_value("MTR010{}.VMAX".format(axis), 5, sleep_after_set=0)
            cls.motor_ca.set_pv_value("MTR010{}.VELO".format(axis), 5, sleep_after_set=0)

        for axis in range(1, 3):
            cls.motor_ca.set_pv_value("MTR020{}.VMAX".format(axis), 5, sleep_after_set=0)
            cls.motor_ca.set_pv_value("MTR020{}.VELO".format(axis), 5, sleep_after_set=0)

    def setUp(self):
        self.ca1D.set_pv_value("COORD0:OFFSET:SP", 0, sleep_after_set=0)
        self.ca1D.assert_that_pv_is("STATIONARY0", 1, timeout=10)

        for axis in range(2):
            self.ca2D.set_pv_value("COORD{}:OFFSET:SP".format(axis), 0, sleep_after_set=0)
            self.ca2D.assert_that_pv_is("STATIONARY{}".format(axis), 1, timeout=10)

        for axis in range(10):
            self.ca10D.set_pv_value("COORD{}:OFFSET:SP".format(axis), 0, sleep_after_set=0)
            self.ca10D.assert_that_pv_is("STATIONARY{}".format(axis), 1, timeout=10)

        for axis in range(1, 9):
            self.motor_ca.set_pv_value("MTR010{}.HLM".format(axis), 100000, sleep_after_set=0)

        for axis in range(1, 3):
            self.motor_ca.set_pv_value("MTR020{}.HLM".format(axis), 100000, sleep_after_set=0)

    def test_GIVEN_1D_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position) in enumerate(POSITIONS_1D):

            self.ca1D.set_pv_value("POSN:SP", expected_position)

            self.ca1D.assert_that_pv_is("POSN:SP:RBV", expected_position)
            self.ca1D.assert_that_pv_is("IPOSN:SP:RBV", index)
            self.motor_ca.assert_that_pv_is("MTR0101.RBV", expected_motor_position)
            self.ca1D.assert_that_pv_is("POSN", expected_position)
            self.ca1D.assert_that_pv_alarm_is("POSN", ChannelAccess.Alarms.NONE)
            self.ca1D.assert_that_pv_is("IPOSN", index)
            self.ca1D.assert_that_pv_is("INPOS{index}".format(index=index), 1)
            self.ca1D.assert_that_pv_is("INPOS{index}".format(index=index+1), 0)
            self.ca1D.assert_that_pv_is("COORD0:IN_POSITION", 1)

    def test_GIVEN_1D_WHEN_set_position_by_index_THEN_position_is_set_and_motor_moves_to_position(self):
        for index, (expected_position, expected_motor_position) in enumerate(POSITIONS_1D):

            self.ca1D.set_pv_value("IPOSN:SP", index)

            self.ca1D.assert_that_pv_is("IPOSN", index)
            self.ca1D.assert_that_pv_is("POSN", expected_position)
            self.motor_ca.assert_that_pv_is("MTR0101.RBV", expected_motor_position)
            self.ca1D.assert_that_pv_is("INPOS{index}".format(index=index), 1)
            self.ca1D.assert_that_pv_is("INPOS{index}".format(index=index + 1), 0)
            self.ca1D.assert_that_pv_is("COORD0:IN_POSITION", 1)

    @parameterized.expand(
        parameterized_list([1, 2, 10])
    )
    def test_GIVEN_XD_WHEN_get_numaxes_THEN_return_X(self, _, axis_num):
        channel_access = self.channel_access_instances[axis_num]
        channel_access.assert_that_pv_is("NUMAXES", axis_num)

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
            self.ca2D.assert_that_pv_is("INPOS{index}".format(index=index), 1)
            self.ca2D.assert_that_pv_is("INPOS{index}".format(index=index + 1), 0)
            self.ca2D.assert_that_pv_is("COORD0:IN_POSITION", 1)
            self.ca2D.assert_that_pv_is("COORD1:IN_POSITION", 1)


    @parameterized.expand(
        parameterized_list([1, 2, 10])
    )
    def test_GIVEN_XD_WHEN_move_to_out_position_THEN_in_position_light_goes_off_then_on(self, _, axis_num):
        first_position = POSITION_TABLES[axis_num][0][0]
        # make sure second position is not a duplicate position of first
        if POSITION_TABLES[axis_num][0][1] != POSITION_TABLES[axis_num][1][1]:
            second_index = 1
        else:
            second_index = 2
        second_position = POSITION_TABLES[axis_num][second_index][0]

        channel_access = self.channel_access_instances[axis_num]
        channel_access.set_pv_value("POSN:SP", first_position)
        channel_access.assert_that_pv_is("POSN", first_position)
        channel_access.set_pv_value("POSN:SP", second_position, sleep_after_set=0)

        for axis in range(axis_num):
            channel_access.assert_that_pv_is("STATIONARY{}".format(axis), 0)
        channel_access.assert_that_pv_is("STATIONARY".format(axis), 0)
        channel_access.assert_that_pv_is("POSITIONED", 0)
        channel_access.assert_that_pv_is("INPOS0", 0)
        channel_access.assert_that_pv_is(f"INPOS{second_index}", 0)

        channel_access.assert_that_pv_is("POSITIONED", 1, timeout=10)
        for axis in range(axis_num):
            channel_access.assert_that_pv_is("STATIONARY{}".format(axis), 1)
        channel_access.assert_that_pv_is("STATIONARY".format(axis), 1)
        channel_access.assert_that_pv_is("INPOS0", 0)
        channel_access.assert_that_pv_is(f"INPOS{second_index}", 1)

    @parameterized.expand(
        parameterized_list([1, 2, 10])
    )
    def test_GIVEN_XD_WHEN_set_offset_THEN_in_position_light_goes_off_then_on_and_motor_moves_to_position_plus_offset(self, _, axis_num):
        channel_access = self.channel_access_instances[axis_num]
        offset_number = 2
        expected_offsets = range(offset_number, axis_num + offset_number)
        expected_motor_positions = POSITION_TABLES[axis_num][0][1:]
        expected_motor_positions = list(map(add, expected_offsets, expected_motor_positions))

        channel_access.set_pv_value("POSN:SP", POSITION_TABLES[axis_num][0][0])
        channel_access.assert_that_pv_is("POSN", POSITION_TABLES[axis_num][0][0])
        channel_access.assert_that_pv_is("POSITIONED", 1)
        channel_access.assert_that_pv_is("INPOS0", 1)
        channel_access.assert_that_pv_is("INPOS1", 0)

        for axis in range(axis_num):
            channel_access.set_pv_value("COORD{}:OFFSET:SP".format(axis), expected_offsets[axis])
        channel_access.assert_that_pv_is("POSITIONED", 0)
        channel_access.assert_that_pv_is("INPOS0", 0)
        channel_access.assert_that_pv_is("INPOS1", 0)

        channel_access.assert_that_pv_is("POSITIONED", 1)
        for axis in range(axis_num):
            channel_access.assert_that_pv_is("COORD{}:OFFSET".format(axis), expected_offsets[axis])
            motor_pv = get_motor_pv_from_axis_num(axis)
            self.motor_ca.assert_that_pv_is("{}.RBV".format(motor_pv), expected_motor_positions[axis])
        channel_access.assert_that_pv_is("INPOS0", 1)
        channel_access.assert_that_pv_is("INPOS1", 0)

    def test_GIVEN_1D_WHEN_set_large_offset_THEN_current_position_set_correctly(self):
        offset = POSITIONS_1D[2][1] - POSITIONS_1D[0][1]
        self.ca1D.set_pv_value("COORD0:OFFSET:SP", -offset)

        self.ca1D.set_pv_value("POSN:SP", POSITION_OUT)

        self.ca1D.assert_that_pv_is("POSITIONED", 0)
        self.ca1D.assert_that_pv_is("POSITIONED", 1)
        self.ca1D.assert_that_pv_is("POSN", POSITION_OUT, timeout=30)

    @parameterized.expand(
        parameterized_list([1, 2, 10])
    )
    def test_GIVEN_XD_WHEN_set_large_offset_THEN_current_position_is_correct(self, _, axis_num):
        axis_num = 1
        channel_access = self.channel_access_instances[axis_num]
        position_table = POSITION_TABLES[axis_num]
        offset_coords = [position_table[0][coord+1] - position_table[2][coord+1] for coord in range(axis_num)]

        for axis in range(axis_num):
            channel_access.set_pv_value("COORD{}:OFFSET:SP".format(axis), -offset_coords[axis])
        channel_access.set_pv_value("POSN:SP", position_table[0][0])

        channel_access.assert_that_pv_is("POSITIONED", 0)
        channel_access.assert_that_pv_is("POSITIONED", 1, timeout=30)
        channel_access.assert_that_pv_is("POSN", position_table[0][0])

    def test_GIVEN_file_WHEN_duplicate_name_value_THEN_load_no_positions(self):
        self.caDN.assert_that_pv_is("POSN:NUM", 0)
        self.caDN.assert_that_pv_is("ERRORMSG", "Duplicate name: \"Sample1\".")   

    @parameterized.expand(
        parameterized_list([1, 2, 10])
    )
    def test_GIVEN_XD_WHEN_invalid_position_specified_THEN_alarm(self, _, axis_num):
        channel_access = self.channel_access_instances[axis_num]
        channel_access.set_pv_value("POSN:SP", "an_invalid_position")
        channel_access.assert_that_pv_alarm_is("POSN:SP", ChannelAccess.Alarms.INVALID)

    @parameterized.expand(
        parameterized_list([1, 2, 10])
    )
    def test_GIVEN_XD_WHEN_move_motor_THEN_tolerance_checked(self, _, axis_num):
        channel_access = self.channel_access_instances[axis_num]
        position_to_test = POSITION_TABLES[axis_num][1]
        channel_access.set_pv_value("TOLERENCE", 10)
        channel_access.set_pv_value("POSN:SP", position_to_test[0])
        self.motor_ca.assert_that_pv_is("MTR0101.RBV", position_to_test[1])
        channel_access.assert_that_pv_is("POSN", position_to_test[0])
        channel_access.assert_that_pv_is("IPOSN", 1)

        # Move motor, all should still be OK as within tolerance
        for axis in range(axis_num):
            motor_pv = get_motor_pv_from_axis_num(axis)
            self.motor_ca.set_pv_value(motor_pv, position_to_test[axis+1] - 0.2)
            self.motor_ca.assert_that_pv_is_number(motor_pv + ".RBV", position_to_test[axis+1] - 0.2, tolerance=.00001)
        channel_access.assert_that_pv_is("POSN", position_to_test[0])
        channel_access.assert_that_pv_is("IPOSN", 1)
        channel_access.assert_that_pv_is("POSITIONED", 1)

        # Change tolerance, should not be in position
        channel_access.set_pv_value("TOLERENCE", 0.1)
        channel_access.assert_that_pv_is("POSN", "")
        channel_access.assert_that_pv_is("IPOSN", -1)
        channel_access.assert_that_pv_is("POSITIONED", 0)

        # Move motor back, should now be in position again
        for axis in range(axis_num):
            motor_pv = get_motor_pv_from_axis_num(axis)
            self.motor_ca.set_pv_value(motor_pv, position_to_test[axis+1])
            self.motor_ca.assert_that_pv_is(motor_pv + ".RBV", position_to_test[axis+1])
        channel_access.assert_that_pv_is("POSN", position_to_test[0])
        channel_access.assert_that_pv_is("IPOSN", 1)
        channel_access.assert_that_pv_is("POSITIONED", 1)

    def _test_alarm_propogates(self, channel_access, motor_num):
        assert_alarm_state_of_posn(channel_access, ChannelAccess.Alarms.NONE)

        # Sets the high limit severity to be MAJOR and sets the high limit to be slightly lower than the current
        # position. This will force the underlying motor into alarm.
        motor_pv = get_motor_pv_from_axis_num(motor_num)
        self.motor_ca.set_pv_value("{}.HLSV".format(motor_pv), ChannelAccess.Alarms.MAJOR)
        current_posn = self.motor_ca.get_pv_value(motor_pv)
        self.motor_ca.set_pv_value("{}.HLM".format(motor_pv), current_posn - 1)
        self.motor_ca.assert_that_pv_alarm_is(motor_pv, ChannelAccess.Alarms.MAJOR)

        assert_alarm_state_of_posn(channel_access, ChannelAccess.Alarms.MAJOR)

    def test_GIVEN_1D_WHEN_axis_in_alarm_THEN_position_in_alarm(self):
        self._test_alarm_propogates(self.ca1D, 0)

    def test_GIVEN_2D_WHEN_second_axis_in_alarm_THEN_position_in_alarm(self):
        self._test_alarm_propogates(self.ca2D, 1)

    @parameterized.expand(
        parameterized_list([3, 6, 9])
    )
    def test_GIVEN_10D_WHEN_various_axis_in_alarm_THEN_position_in_alarm(self, _, axis):
        self._test_alarm_propogates(self.ca10D, axis)

    def test_GIVEN_10D_WHEN_set_position_THEN_position_is_set_and_motor_moves_to_position(self):
        def check_motor_positions(expected_coords, readback):
            pv_suffix = ".RBV" if readback else ""
            timeout = 10 if readback else 0.1
            for index, coord in enumerate(expected_coords):
                motor_pv = get_motor_pv_from_axis_num(index) + pv_suffix
                self.motor_ca.assert_that_pv_is_number(motor_pv, coord, timeout=timeout)

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
            self.ca10D.assert_that_pv_is("INPOS{index}".format(index=sample_num), 1)
            self.ca10D.assert_that_pv_is("INPOS{index}".format(index=sample_num + 1), 0)

    def test_GIVEN_10D_WHEN_units_of_motor_set_THEN_units_of_coordinates_also_set(self):
        motor_pvs = ["MTR010{}".format(i) for i in range(1, 9)]
        motor_pvs.extend(["MTR0201", "MTR0202"])

        for motor_num, motor_pv in enumerate(motor_pvs):
            # Set motor unit to PV name
            self.motor_ca.set_pv_value("{}.EGU".format(motor_pv), motor_pv)

            self.ca10D.assert_that_pv_is("COORD{}.EGU".format(motor_num), motor_pv)
            self.ca10D.assert_that_pv_is("COORD{}:RBV.EGU".format(motor_num), motor_pv)
            self.ca10D.assert_that_pv_is("COORD{}:NO_OFF.EGU".format(motor_num), motor_pv)
            self.ca10D.assert_that_pv_is("COORD{}:OFFSET.EGU".format(motor_num), motor_pv)
            self.ca10D.assert_that_pv_is("COORD{}:OFFSET:SP.EGU".format(motor_num), motor_pv)
            self.ca10D.assert_that_pv_is("COORD{}:RBV:OFF.EGU".format(motor_num), motor_pv)
            self.ca10D.assert_that_pv_is("COORD{}:SET:RBV.EGU".format(motor_num), motor_pv)

    def test_WHEN_lookup_modified_and_reset_called_THEN_new_position_names_picked_up(self):
        lookup_file = os.path.join(test_path, "lookup10D.txt")
        new_position_name = "NOT_Sample1"

        self.assertTrue(new_position_name not in self.ca10D.get_pv_value("POSITIONS"))

        def test_position_updated():
            self.assertTrue(new_position_name in self.ca10D.get_pv_value("POSITIONS"))

        modify_file_and_assert_test(self.ca10D, lookup_file, "Sample1", new_position_name, test_position_updated)

    def test_WHEN_lookup_modified_to_be_in_error_and_reset_called_THEN_new_position_names_picked_up(self):
        lookup_file = os.path.join(test_path, "lookup10D.txt")

        def test_position_empty():
            self.ca10D.assert_that_pv_is("POSITIONS", "", timeout=30)
            self.ca10D.assert_that_pv_is("POSN", "", timeout=30)

        modify_file_and_assert_test(self.ca10D, lookup_file, "Sample1", "", test_position_empty)

    def test_GIVEN_in_position_WHEN_lookup_modified_and_reset_called_THEN_no_longer_in_position(self):
        lookup_file = os.path.join(test_path, "lookup2D.txt")
        new_coord = 7

        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)

        self.ca2D.assert_that_pv_is("POSITIONED", 1, timeout=10)
        self.ca2D.assert_that_pv_is("POSN:SP:RBV", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)

        def test_not_in_position():
            self.ca2D.assert_that_pv_is("POSITIONED", 0, timeout=10)
            self.ca2D.assert_that_pv_is_not("POSN", POSITION_SAMPLE1)
            self.ca2D.assert_that_pv_is("POSN:SP:RBV", POSITION_SAMPLE1)
            self.motor_ca.assert_that_pv_is("MTR0101.RBV", MOTOR_POSITION_SAMPLE1_COORD0)
            self.motor_ca.assert_that_pv_is("MTR0102.RBV", MOTOR_POSITION_SAMPLE1_COORD1)

        modify_file_and_assert_test(self.ca2D, lookup_file, MOTOR_POSITION_SAMPLE1_COORD1, new_coord,
                                    test_not_in_position)

    def test_GIVEN_in_position_WHEN_lookup_modified_and_move_to_updated_position_THEN_go_to_new_position(self):
        lookup_file = os.path.join(test_path, "lookup2D.txt")
        new_coord = 7

        self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE1)

        self.ca2D.assert_that_pv_is("POSITIONED", 1, timeout=10)
        self.ca2D.assert_that_pv_is("POSN:SP:RBV", POSITION_SAMPLE1)
        self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE1)

        def test_moves_to_new_position():
            self.ca2D.set_pv_value("POSN:SP", POSITION_SAMPLE2)
            self.ca2D.assert_that_pv_is("POSITIONED", 1, timeout=10)
            self.ca2D.assert_that_pv_is("POSN:SP:RBV", POSITION_SAMPLE2)
            self.ca2D.assert_that_pv_is("POSN", POSITION_SAMPLE2)
            self.motor_ca.assert_that_pv_is("MTR0101.RBV", MOTOR_POSITION_SAMPLE2_COORD0)
            self.motor_ca.assert_that_pv_is("MTR0102.RBV", new_coord)

        modify_file_and_assert_test(self.ca2D, lookup_file, MOTOR_POSITION_SAMPLE2_COORD1, new_coord,
                                    test_moves_to_new_position)

    def test_GIVEN_2D_WHEN_coords_set_through_motion_set_points_THEN_underlying_axis_moves(self):
        for coord in range(2):
            new_position = 5 + coord
            self.ca2D.assert_setting_setpoint_sets_readback(new_position, f"COORD{coord}:RBV", f"COORD{coord}:SP")
            self.motor_ca.assert_that_pv_is(f"MTR010{coord+1}.RBV", new_position)

    def test_GIVEN_files_WHEN_file_names_checked_THEN_current_names_correct(self):
        self.ca1D.assert_that_pv_is("FILENAME", "lookup1D.txt")
        self.ca2D.assert_that_pv_is("FILENAME", "lookup2D.txt")
        self.ca10D.assert_that_pv_is("FILENAME", "lookup10D.txt")
        self.caDN.assert_that_pv_is("FILENAME", "duplicate_names.txt")
        self.caDP.assert_that_pv_is("FILENAME", "duplicate_positions.txt")
