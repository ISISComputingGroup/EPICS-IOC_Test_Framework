from __future__ import division

import unittest
import os
from time import sleep

from genie_python.channel_access_exceptions import WriteAccessException
from parameterized import parameterized

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.axis import assert_axis_moving, assert_axis_not_moving
from utils.testing import parameterized_list, ManagerMode
from math import ceil

try:
    from contextlib import nullcontext
except ImportError:
    from contextlib2 import nullcontext

test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "motorExtensions", "master", "settings", "sans2d")
)

GALIL_ADDR = "127.0.0.1"

# Create GALIL_03, GALIL_04 and GALIL_05
IOCS = [
    {
        "name": "GALIL_0{}".format(i),
        "directory": get_default_ioc_dir("GALIL", i),
        "custom_prefix": "MOT",
        "pv_for_existence": "MTR0{}01".format(i),
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "0{}".format(i),
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        }
    } for i in [3, 4, 5]
]

IOCS.append(
        {
            "name": "INSTETC",
            "directory": get_default_ioc_dir("INSTETC"),
            "custom_prefix": "CS",
            "pv_for_existence": "MANAGER",
        })

TEST_MODES = [TestModes.RECSIM]


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


class Sans2dVacCollisionAvoidanceTests(unittest.TestCase):
    """
    Tests for the sans2d vacuum tank motor extensions.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix="MOT", default_timeout=30)
        with ManagerMode(ChannelAccess()):
            self._disable_collision_avoidance()

            for axis in BAFFLES_AND_DETECTORS_Z_AXES:
                current_position = self.ca.get_pv_value("{}".format(axis))

                new_position = self._get_axis_default_position("{}".format(axis))

                self.ca.set_pv_value("{}:MTR.VMAX".format(axis), TEST_SPEED, sleep_after_set=0)
                self.ca.set_pv_value("{}:MTR.VELO".format(axis), TEST_SPEED, sleep_after_set=0)
                self.ca.set_pv_value("{}:MTR.ACCL".format(axis), TEST_ACCELERATION, sleep_after_set=0)

                if current_position != new_position:
                    self.ca.set_pv_value("{}:SP".format(axis), new_position, sleep_after_set=0)

                timeout = self._get_timeout_for_moving_to_position(axis, new_position)
                self.ca.assert_that_pv_is("{}".format(axis), new_position, timeout=timeout)

            # re-enable collision avoidance
            self._enable_collision_avoidance()

    def _disable_collision_avoidance(self):
        self._set_collision_avoidance_state(1, "DISABLED")

    def _enable_collision_avoidance(self):
        self._set_collision_avoidance_state(0, "ENABLED")

    def _set_collision_avoidance_state(self, write_value, read_value):

        # Do nothing if manager mode is already in correct state
        if ChannelAccess().get_pv_value(ManagerMode.MANAGER_MODE_PV) != "Yes":
            cm = ManagerMode(ChannelAccess())
        else:
            cm = nullcontext()

        with cm:
            err = None
            for _ in range(20):
                try:
                    self.ca.set_pv_value("SANS2DVAC:COLLISION_AVOIDANCE", write_value, sleep_after_set=0)
                    break
                except WriteAccessException as e:
                    err = e
                    sleep(1)
            else:
                raise err
            self.ca.assert_that_pv_is("SANS2DVAC:COLLISION_AVOIDANCE", read_value)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_motor_interval_above_minor_warning_threshold_THEN_interval_is_correct_and_not_in_alarm(self, _, axis_pair):
        # disable collision avoidance so it does not interfere with checking the intervals and their alarm status
        self._disable_collision_avoidance()

        rear_axis_position = self.ca.get_pv_value(axis_pair.rear_axis)
        front_axis_position = rear_axis_position - 50 - MINOR_ALARM_INTERVAL_THRESHOLD
        expected_interval = rear_axis_position - front_axis_position

        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_position, sleep_after_set=0)

        timeout = self._get_timeout_for_moving_to_position(axis_pair.front_axis, front_axis_position)
        self.ca.assert_that_pv_is_number("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), expected_interval, timeout=timeout, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_setpoint_interval_above_minor_warning_threshold_THEN_interval_is_correct_and_not_in_alarm(self, _, axis_pair):
        # disable collision avoidance so it does not interfere with checking the intervals and their alarm status
        self._disable_collision_avoidance()

        rear_axis_position = 1000
        front_axis_position = rear_axis_position - 50 - MINOR_ALARM_INTERVAL_THRESHOLD
        expected_interval = rear_axis_position - front_axis_position

        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_position, sleep_after_set=0)
        self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_position, sleep_after_set=0)
        self._assert_axis_position_reached(axis_pair.front_axis, front_axis_position)
        self._assert_axis_position_reached(axis_pair.rear_axis, rear_axis_position)

        self.ca.assert_that_pv_is_number("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), expected_interval, timeout=5, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_motor_interval_under_minor_warning_threshold_THEN_interval_is_correct_and_in_minor_alarm(self, _, axis_pair):
        # disable collision avoidance so it does not interfere with checking the intervals and their alarm status
        self._disable_collision_avoidance()

        rear_position = self.ca.get_pv_value(axis_pair.rear_axis)
        front_new_position = rear_position - MINOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = rear_position - front_new_position

        self.ca.set_pv_value(axis_pair.front_axis_sp, front_new_position, sleep_after_set=0)

        timeout = self._get_timeout_for_moving_to_position(axis_pair.front_axis, front_new_position)
        self.ca.assert_that_pv_is_number("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), expected_interval, timeout=timeout, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_setpoint_interval_under_minor_warning_threshold_THEN_interval_is_correct_and_in_minor_alarm(self, _, axis_pair):
        # disable collision avoidance so it does not interfere with checking the intervals and their alarm status
        self._disable_collision_avoidance()

        rear_axis_position = 1000
        front_axis_position = rear_axis_position - MINOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = rear_axis_position - front_axis_position

        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_position, sleep_after_set=0)
        self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_position, sleep_after_set=0)
        self._assert_axis_position_reached(axis_pair.front_axis, front_axis_position)
        self._assert_axis_position_reached(axis_pair.rear_axis, rear_axis_position)

        self.ca.assert_that_pv_is_number("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), expected_interval, timeout=5, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_motor_interval_under_major_warning_threshold_THEN_interval_is_correct_and_in_major_alarm(self, _, axis_pair):
        # disable collision avoidance so it does not interfere with checking the intervals and their alarm status
        self._disable_collision_avoidance()

        rear_axis_position = self.ca.get_pv_value(axis_pair.rear_axis)
        front_axis_position = rear_axis_position - MAJOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = rear_axis_position - front_axis_position

        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_position, sleep_after_set=0)

        timeout = self._get_timeout_for_moving_to_position(axis_pair.front_axis, front_axis_position)
        self.ca.assert_that_pv_is_number("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), expected_interval, timeout=timeout, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), self.ca.Alarms.MAJOR)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_setpoint_interval_under_major_warning_threshold_THEN_interval_is_correct_and_in_major_alarm(self, _, axis_pair):
        # disable collision avoidance so it does not interfere with checking the intervals and their alarm status
        self._disable_collision_avoidance()

        rear_axis_position = 1000
        front_axis_position = rear_axis_position - MAJOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = rear_axis_position - front_axis_position

        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_position, sleep_after_set=0)
        self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_position, sleep_after_set=0)

        self._assert_axis_position_reached(axis_pair.front_axis, front_axis_position)
        self._assert_axis_position_reached(axis_pair.rear_axis, rear_axis_position)

        self.ca.assert_that_pv_is_number("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), expected_interval, timeout=5, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(axis_pair.name), self.ca.Alarms.MAJOR)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_front_axis_moves_towards_rear_axis_WHEN_setpoint_interval_greater_than_threshold_THEN_motor_not_stopped(self, _, axis_pair):
        front_axis_new_position = (self.ca.get_pv_value(axis_pair.rear_axis) - axis_pair.minimum_interval) - 50
        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_new_position, sleep_after_set=0)

        self._assert_axis_position_reached(axis_pair.front_axis, front_axis_new_position)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_front_axis_moves_towards_rear_axis_WHEN_setpoint_interval_smaller_than_threshold_THEN_motor_stops(self, _, axis_pair):
        front_axis_new_position = (self.ca.get_pv_value(axis_pair.rear_axis) - axis_pair.minimum_interval) + 50
        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_new_position, sleep_after_set=0)

        self.ca.assert_that_pv_is("{}:MTR.MOVN".format(axis_pair.front_axis), 1, timeout=1)
        self.ca.assert_that_pv_is("{}:MTR.TDIR".format(axis_pair.front_axis), 1, timeout=1)

        timeout = self._get_timeout_for_moving_to_position(axis_pair.front_axis, front_axis_new_position)
        assert_axis_not_moving(axis_pair.front_axis, timeout=timeout)
        self.ca.assert_that_pv_is_not(axis_pair.front_axis, front_axis_new_position, timeout=timeout)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_front_axis_within_threhsold_distance_to_rear_axis_WHEN_set_to_move_away_THEN_motor_not_stopped(self, _, axis_pair):
        front_axis_new_position = (self.ca.get_pv_value(axis_pair.rear_axis) - axis_pair.minimum_interval) + 50
        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_new_position, sleep_after_set=0)

        self.ca.assert_that_pv_is("{}:MTR.MOVN".format(axis_pair.front_axis), 1, timeout=1)
        self.ca.assert_that_pv_is("{}:MTR.TDIR".format(axis_pair.front_axis), 1, timeout=1)

        timeout = self._get_timeout_for_moving_to_position(axis_pair.front_axis, front_axis_new_position)
        assert_axis_not_moving(axis_pair.front_axis, timeout=timeout)
        self.ca.assert_that_pv_is_not(axis_pair.front_axis, front_axis_new_position, timeout=timeout)

        front_axis_new_position = self.ca.get_pv_value(axis_pair.front_axis) - 200
        self.ca.set_pv_value(axis_pair.front_axis_sp, front_axis_new_position, sleep_after_set=0)

        assert_axis_moving(axis_pair.front_axis, timeout=1)
        self.ca.assert_that_pv_is("{}:MTR.TDIR".format(axis_pair.front_axis), 0, timeout=1)
        self._assert_axis_position_reached(axis_pair.front_axis, front_axis_new_position)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_rear_axis_moves_towards_front_axis_WHEN_setpoint_interval_greater_than_threshold_THEN_motor_not_stopped(self, _, axis_pair):
        rear_axis_position = (self.ca.get_pv_value(axis_pair.front_axis) + axis_pair.minimum_interval) + 50
        self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_position, sleep_after_set=0)

        self._assert_axis_position_reached(axis_pair.rear_axis, rear_axis_position)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_rear_axis_moves_towards_front_axis_WHEN_setpoint_interval_smaller_than_threshold_THEN_motor_stops(self, _, axis_pair):
        rear_axis_new_position = (self.ca.get_pv_value(axis_pair.front_axis) + axis_pair.minimum_interval) - 50
        self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_new_position, sleep_after_set=0)

        self.ca.assert_that_pv_is("{}:MTR.MOVN".format(axis_pair.rear_axis), 1, timeout=1)
        self.ca.assert_that_pv_is("{}:MTR.TDIR".format(axis_pair.rear_axis), 0, timeout=1)

        timeout = self._get_timeout_for_moving_to_position(axis_pair.rear_axis, rear_axis_new_position)
        assert_axis_not_moving(axis_pair.rear_axis, timeout=timeout)
        self.ca.assert_that_pv_is_not(axis_pair.rear_axis, rear_axis_new_position, timeout=timeout)

    @parameterized.expand(parameterized_list(AXIS_PAIRS))
    def test_GIVEN_rear_axis_within_threhsold_distance_to_front_axis_WHEN_set_to_move_away_THEN_motor_not_stopped(self, _, axis_pair):
        rear_axis_new_position = (self.ca.get_pv_value(axis_pair.front_axis) + axis_pair.minimum_interval) - 50
        self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_new_position, sleep_after_set=0)

        self.ca.assert_that_pv_is("{}:MTR.MOVN".format(axis_pair.rear_axis), 1, timeout=1)
        self.ca.assert_that_pv_is("{}:MTR.TDIR".format(axis_pair.rear_axis), 0, timeout=1)

        timeout = self._get_timeout_for_moving_to_position(axis_pair.rear_axis, rear_axis_new_position)
        assert_axis_not_moving(axis_pair.rear_axis, timeout=timeout)
        self.ca.assert_that_pv_is_not(axis_pair.rear_axis, rear_axis_new_position, timeout=timeout)

        rear_axis_new_position = self.ca.get_pv_value(axis_pair.rear_axis) + 200
        self.ca.set_pv_value(axis_pair.rear_axis_sp, rear_axis_new_position, sleep_after_set=0)

        assert_axis_moving(axis_pair.rear_axis, timeout=1)
        self.ca.assert_that_pv_is("{}:MTR.TDIR".format(axis_pair.rear_axis), 1, timeout=1)
        self._assert_axis_position_reached(axis_pair.rear_axis, rear_axis_new_position)

    def _get_axis_default_position(self, axis):
        if axis == "FRONTDETZ":
            new_position = 1000
        elif axis == "FRONTBAFFLEZ":
            new_position = 3000
        elif axis == "REARBAFFLEZ":
            new_position = 5000
        elif axis == "REARDETZ":
            new_position = 7000
        else:
            raise ValueError("invalid axis!")

        return new_position

    def _get_timeout_for_moving_to_position(self, moving_axis, new_position):
        distance_to_travel = abs(new_position - self.ca.get_pv_value(moving_axis))

        time_to_accelerate_and_decelerate = 2 * TEST_ACCELERATION

        # between 0 and full speed, the average speed is half the full speed, same for when decelerating.
        # Therefore, the distance traveled when accelerating and decelerating is
        # 2 * (full_speed/2 * acceleration_time), so full_speed / acceleration_time
        time_at_full_speed = (distance_to_travel - TEST_SPEED * TEST_ACCELERATION) / TEST_SPEED

        total_time = ceil(time_to_accelerate_and_decelerate + time_at_full_speed)

        return total_time + 10  # +10 as a small tolerance to avoid instability

    def _assert_axis_position_reached(self, axis, position):
        timeout = self._get_timeout_for_moving_to_position(axis, position)
        self.ca.assert_that_pv_is_number(axis, position, tolerance=0.1, timeout=timeout)
