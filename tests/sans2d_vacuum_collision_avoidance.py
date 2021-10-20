import unittest
import os

from genie_python.channel_access_exceptions import WriteAccessException
from parameterized import parameterized

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.axis import assert_axis_not_moving
from utils.testing import parameterized_list, ManagerMode

try:
    from contextlib import nullcontext
except ImportError:
    from contextlib2 import nullcontext

test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "motorExtensions", "master", "settings", "sans2d_vacuum_tank")
)

GALIL_ADDR1 = "127.0.0.3"
GALIL_ADDR2 = "127.0.0.2"
GALIL_ADDR3 = "127.0.0.0"

# Create GALIL_03, GALIL_04 and GALIL_05
IOCS = [
    {
        "name": "GALIL_03",
        "directory": get_default_ioc_dir("GALIL", 3),
        "custom_prefix": "MOT",
        "pv_for_existence": "MTR0301",
        "macros": {
            "GALILADDR": GALIL_ADDR1,
            "MTRCTRL": "03",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        }
    },
    {
        "name": "GALILMUL_02",
        "directory": get_default_ioc_dir("GALILMUL", 2),
        "custom_prefix": "MOT",
        "pv_for_existence": "MTR0401",
        "macros": {
            "MTRCTRL1": "04",
            "GALILADDR1": GALIL_ADDR2,
            "MTRCTRL2": "05",
            "GALILADDR2": GALIL_ADDR3,
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        }
    },
    {
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    }
]

TEST_MODES = [TestModes.RECSIM]

ERRORS = {
    "FDFB": "Front Det & baffle collision detected",
    "FBRB": "Front & rear baffle collision detected",
    "RBRD": "Rear baffle & det collision detected"
}


class AxisPair(object):
    def __init__(self, front_axis, rear_axis, name, interval_setpoint_name, minimum_interval):
        self.front_axis = front_axis
        self.front_axis_sp = front_axis + ":SP"
        self.rear_axis = rear_axis
        self.rear_axis_sp = rear_axis + ":SP"
        self.name = name
        self.setpoint_name = interval_setpoint_name
        self.minimum_interval = minimum_interval

    def __repr__(self):
        return "Interval between {} and {}".format(self.front_axis, self.rear_axis)


AXIS_PAIRS = [
    AxisPair(front_axis="FRONTDETZ", rear_axis="FRONTBAFFLEZ",
             name="FDFB", interval_setpoint_name="FDSPFBSP", minimum_interval=1050),
    AxisPair(front_axis="FRONTBAFFLEZ", rear_axis="REARBAFFLEZ",
             name="FBRB", interval_setpoint_name="FBSPRBSP", minimum_interval=210),
    AxisPair(front_axis="REARBAFFLEZ", rear_axis="REARDETZ",
             name="RBRD", interval_setpoint_name="RBSPRDSP", minimum_interval=350),
]

BAFFLES_AND_DETECTORS_Z_AXES = set(
    [interval.front_axis for interval in AXIS_PAIRS] + [interval.rear_axis for interval in AXIS_PAIRS])

MAJOR_ALARM_INTERVAL_THRESHOLD = 50
MINOR_ALARM_INTERVAL_THRESHOLD = 100

TEST_SPEED = 200
# acceleration is number of seconds until motor goes from 0 to full speed
TEST_ACCELERATION = 0

FRONTDET_INITIAL_POS = 100


class Sans2dVacCollisionAvoidanceTests(unittest.TestCase):
    """
    Tests for the sans2d vacuum tank motor extensions.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix="MOT", default_timeout=30)
        self.ca.set_pv_value("SANS2DVAC:STOP_MOTORS:ALL.PROC", 1)
        with ManagerMode(ChannelAccess()):
            for axis in BAFFLES_AND_DETECTORS_Z_AXES:
                self.ca.set_pv_value("{}:MTR.VMAX".format(axis), TEST_SPEED)
                self.ca.set_pv_value("{}:MTR.VELO".format(axis), TEST_SPEED)
                self.ca.set_pv_value("{}:MTR.ACCL".format(axis), TEST_ACCELERATION)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_setpoint_for_each_axis_THEN_axis_not_moved(self, _, axis_pair):
        front_axis_new_position = 0
        self.ca.set_pv_value(axis_pair.front_axis_sp,
                             self.ca.get_pv_value(axis_pair.front_axis_sp) + front_axis_new_position)
        assert_axis_not_moving(axis_pair.front_axis)
        self.ca.set_pv_value(axis_pair.rear_axis_sp,
                             (self.ca.get_pv_value(axis_pair.front_axis_sp) + axis_pair.minimum_interval) + 50)
        assert_axis_not_moving(axis_pair.front_axis)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_front_axis_moves_towards_rear_axis_WHEN_setpoint_interval_smaller_than_threshold_THEN_warning_message_is_available(
            self, _, axis_pair):
        front_axis_new_position = (self.ca.get_pv_value(axis_pair.rear_axis) - axis_pair.minimum_interval) + 50
        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_new_position)

        error_message = self.ca.get_pv_value("SANS2DVAC:{}_COLLISION".format(axis_pair.name))
        self.assertEquals(error_message, ERRORS[axis_pair.name])

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_front_axis_moves_towards_rear_axis_WHEN_setpoint_interval_smaller_than_threshold_THEN_warning_message_is_not_available(
            self, _, axis_pair):
        front_axis_new_position = (self.ca.get_pv_value(axis_pair.rear_axis_sp) - axis_pair.minimum_interval) - 51
        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_new_position, sleep_after_set=1)

        error_message = self.ca.get_pv_value("SANS2DVAC:{}_COLLISION".format(axis_pair.name))
        self.assertEquals(error_message, "")

    def test_GIVEN_all_positions_valid_WHEN_move_all_THEN_all_axes_moved(self):
        # set front det initial position
        self.ca.set_pv_value("FRONTDETZ:SP", 100)
        end_values = {"FRONTDETZ": 100}
        for axis_pair in AXIS_PAIRS:
            rear_axis_pos = (self.ca.get_pv_value(axis_pair.front_axis_sp) + axis_pair.minimum_interval) + 50
            end_values[axis_pair.rear_axis] = rear_axis_pos
            self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_pos)

        self.ca.set_pv_value("SANS2DVAC:MOVE_ALL.PROC", 1, sleep_after_set=10)
        for key in end_values.keys():
            self.assertEquals(end_values[key], self.ca.get_pv_value(key))

    def test_GIVEN_positions_invalid_WHEN_move_all_THEN_axes_movement_is_inhibited(self):
        for axis_pair in AXIS_PAIRS:
            rear_axis_pos = (self.ca.get_pv_value(axis_pair.front_axis_sp) + axis_pair.minimum_interval) - 50
            self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_pos)

        with self.assertRaises(WriteAccessException, msg="DISP should be set on inhibited axis"):
            self.ca.set_pv_value("SANS2DVAC:MOVE_ALL.PROC", 1, sleep_after_set=10)

    def test_GIVEN_some_positions_invalid_WHEN_move_all_THEN_axes_movement_is_inhibited(self):
        # invalid, invalid, valid, valid positions
        positions = {"FRONTDETZ": 100, "FRONTBAFFLEZ": 200, "REARBAFFLEZ": 500, "REARDETZ": 1000}
        for axis_pair in AXIS_PAIRS:
            self.ca.set_pv_value(axis_pair.rear_axis_sp, positions[axis_pair.rear_axis])

        with self.assertRaises(WriteAccessException, msg="DISP should be set on inhibited axis"):
            self.ca.set_pv_value("SANS2DVAC:MOVE_ALL.PROC", 1, sleep_after_set=10)

    def test_GIVEN_some_axis_are_moving_THEN_not_possible_to_change_SP(self):
        positions = {"FRONTDETZ": 5000, "FRONTBAFFLEZ": 6100, "REARBAFFLEZ": 7500, "REARDETZ": 8000}
        for axis_position in positions:
            self.ca.set_pv_value(axis_position + ":SP", positions[axis_position])

        self.ca.set_pv_value("SANS2DVAC:MOVE_ALL.PROC", 1)

        for axis_position in positions:
            with self.assertRaises(WriteAccessException, msg="DISP should be set on inhibited axis"):
                self.ca.set_pv_value(axis_position + ":SP", positions[axis_position])

            with self.assertRaises(WriteAccessException, msg="DISP should be set on inhibited axis"):
                self.ca.set_pv_value(axis_position + ":MTR", positions[axis_position])

    @parameterized.expand(parameterized_list(BAFFLES_AND_DETECTORS_Z_AXES))
    def test_GIVEN_some_axes_have_stopped_moving_THEN_stopped_axes_are_set_to_PAUSE(self, _, axis):

        self.ca.set_pv_value("{}:MTR.VMAX".format(axis), 1)
        self.ca.set_pv_value("{}:MTR.VELO".format(axis), 1)
        self.ca.set_pv_value("{}:MTR.ACCL".format(axis), 1)

        global FRONTDET_INITIAL_POS
        FRONTDET_INITIAL_POS = FRONTDET_INITIAL_POS + 100
        self.ca.set_pv_value("FRONTDETZ:SP", FRONTDET_INITIAL_POS)

        for axis_pair in AXIS_PAIRS:
            self.ca.set_pv_value(axis_pair.rear_axis_sp, self.ca.get_pv_value(axis_pair.front_axis_sp)
                                 + axis_pair.minimum_interval + 500)

        self.ca.set_pv_value("SANS2DVAC:MOVE_ALL.PROC", 1, sleep_after_set=5)

        for tank_axis in BAFFLES_AND_DETECTORS_Z_AXES:
            if tank_axis in axis:
                self.ca.assert_that_pv_is("{}:MTR.SPMG".format(tank_axis), "Move")
            else:
                self.ca.assert_that_pv_is("{}:MTR.SPMG".format(tank_axis), "Pause")

        self.ca.set_pv_value("SANS2DVAC:STOP_MOTORS:ALL.PROC", 1)

        self.ca.set_pv_value("{}:MTR.VMAX".format(axis), TEST_SPEED)
        self.ca.set_pv_value("{}:MTR.VELO".format(axis), TEST_SPEED)
        self.ca.set_pv_value("{}:MTR.ACCL".format(axis), TEST_ACCELERATION)
