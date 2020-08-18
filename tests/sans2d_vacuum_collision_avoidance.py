from __future__ import division

import unittest
import os
from parameterized import parameterized

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.axis import set_axis_moving, assert_axis_moving, assert_axis_not_moving
from utils.testing import parameterized_list, ManagerMode
from math import ceil

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

INTERVAL_PAIRS = [("FRONTDETZ", "FRONTBAFFLEZ"), ("FRONTBAFFLEZ", "REARBAFFLEZ"), ("REARBAFFLEZ", "REARDETZ"), ]

INTERVAL_SETPOINT_PAIRS = [("FRONTDETZ:SP", "FRONTBAFFLEZ:SP"), ("FRONTBAFFLEZ:SP", "REARBAFFLEZ:SP"),
                           ("REARBAFFLEZ:SP", "REARDETZ:SP")]

BAFFLE_AND_DETECTORS_INTERVAL_NAMES = ["FDFB", "FBRB", "RBRD"]

BAFFLE_AND_DETECTORS_INTERVAL_SETPOINT_NAMES = ["FDSPFBSP", "FBSPRBSP", "RBSPRDSP"]

BAFFLES_AND_DETECTORS_Z_AXES = ["REARDETZ", "REARBAFFLEZ", "FRONTBAFFLEZ", "FRONTDETZ"]

MAJOR_ALARM_INTERVAL_THRESHOLD = 50
MINOR_ALARM_INTERVAL_THRESHOLD = 100

FD_FB_MINIMUM_INTERVAL = 150
FB_RB_MINIMUM_INTERVAL = 210
RB_RD_MINIMUM_INTERVAL = 350

TEST_SPEED = 200
# acceleration is number of seconds until motor goes from 0 to full speed
TEST_ACCELERATION = 1


class Sans2dVacCollisionAvoidanceTests(unittest.TestCase):
    """
    Tests for the sans2d vacuum tank motor extensions.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix="MOT")
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("SANS2DVAC:COLLISION_AVOIDANCE", 1)

            for axis in BAFFLES_AND_DETECTORS_Z_AXES:
                current_position = self.ca.get_pv_value("{}".format(axis))

                new_position = self._get_axis_default_position("{}".format(axis))

                self.ca.set_pv_value("{}:MTR.VMAX".format(axis), TEST_SPEED)
                self.ca.set_pv_value("{}:MTR.VELO".format(axis), TEST_SPEED)
                self.ca.set_pv_value("{}:MTR.ACCL".format(axis), TEST_ACCELERATION)

                if current_position != new_position:
                    self.ca.set_pv_value("{}:SP".format(axis), new_position)

                timeout = self._get_timeout_for_moving_to_position(axis, new_position)
                self.ca.assert_that_pv_is("{}".format(axis), new_position, timeout=timeout)

    @parameterized.expand(parameterized_list(zip(INTERVAL_PAIRS, BAFFLE_AND_DETECTORS_INTERVAL_NAMES)))
    def test_GIVEN_motor_interval_above_minor_warning_threshold_THEN_interval_is_correct_and_not_in_alarm(self, _, z_axes_pair, interval_name):
        z_axis_a, z_axis_b = z_axes_pair

        b_position = self.ca.get_pv_value(z_axis_b)
        a_new_position = b_position - 50 - MINOR_ALARM_INTERVAL_THRESHOLD
        expected_interval = b_position - a_new_position

        self.ca.set_pv_value("{}:SP".format(z_axis_a), a_new_position)

        timeout = self._get_timeout_for_moving_to_position(z_axis_a, a_new_position)
        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=timeout)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(zip(INTERVAL_SETPOINT_PAIRS,
                                                 BAFFLE_AND_DETECTORS_INTERVAL_SETPOINT_NAMES)))
    def test_GIVEN_setpoint_interval_above_minor_warning_threshold_THEN_interval_is_correct_and_not_in_alarm(self, _, z_axes_pair, interval_name):
        z_axis_a, z_axis_b = z_axes_pair

        b_position = 1000
        a_position = b_position - 50 - MINOR_ALARM_INTERVAL_THRESHOLD
        expected_interval = b_position - a_position

        self.ca.set_pv_value(z_axis_a, a_position)
        self.ca.set_pv_value(z_axis_b, b_position)

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=5)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(zip(INTERVAL_PAIRS, BAFFLE_AND_DETECTORS_INTERVAL_NAMES)))
    def test_GIVEN_motor_interval_under_minor_warning_threshold_THEN_interval_is_correct_and_in_minor_alarm(self, _, z_axes_pair, interval_name):
        z_axis_a, z_axis_b = z_axes_pair

        b_position = self.ca.get_pv_value(z_axis_b)
        a_new_position = b_position - MINOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = b_position - a_new_position

        self.ca.set_pv_value("{}:SP".format(z_axis_a), a_new_position)

        timeout = self._get_timeout_for_moving_to_position(z_axis_a, a_new_position)
        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=timeout)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list(zip(INTERVAL_SETPOINT_PAIRS,
                                                 BAFFLE_AND_DETECTORS_INTERVAL_SETPOINT_NAMES)))
    def test_GIVEN_setpoint_interval_under_minor_warning_threshold_THEN_interval_is_correct_and_in_minor_alarm(self, _, z_axes_pair, interval_name):
        z_axis_a, z_axis_b = z_axes_pair

        b_position = 1000
        a_position = b_position - MINOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = b_position - a_position

        self.ca.set_pv_value(z_axis_a, a_position)
        self.ca.set_pv_value(z_axis_b, b_position)

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=5)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list(zip(INTERVAL_PAIRS, BAFFLE_AND_DETECTORS_INTERVAL_NAMES)))
    def test_GIVEN_motor_interval_under_major_warning_threshold_THEN_interval_is_correct_and_in_major_alarm(self, _, z_axes_pair, interval_name):
        z_axis_a, z_axis_b = z_axes_pair

        b_position = self.ca.get_pv_value(z_axis_b)
        a_new_position = b_position - MAJOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = b_position - a_new_position

        self.ca.set_pv_value("{}:SP".format(z_axis_a), a_new_position)

        timeout = self._get_timeout_for_moving_to_position(z_axis_a, a_new_position)
        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=timeout)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.MAJOR)

    @parameterized.expand(parameterized_list(zip(INTERVAL_SETPOINT_PAIRS,
                                                 BAFFLE_AND_DETECTORS_INTERVAL_SETPOINT_NAMES)))
    def test_GIVEN_setpoint_interval_under_major_warning_threshold_THEN_interval_is_correct_and_in_major_alarm(self, _, z_axes_pair, interval_name):
        z_axis_a, z_axis_b = z_axes_pair

        b_position = 1000
        a_position = b_position - MAJOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = b_position - a_position

        self.ca.set_pv_value(z_axis_a, a_position)
        self.ca.set_pv_value(z_axis_b, b_position)

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=5)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.MAJOR)

    def test_GIVEN_front_detector_moves_towards_front_baffle_WHEN_setpoint_interval_greater_than_threshold_THEN_motor_not_stopped(self):
        fd_new_position = self.ca.get_pv_value("FRONTBAFFLEZ") - FD_FB_MINIMUM_INTERVAL - 50
        self.ca.set_pv_value("FRONTDETZ:SP", fd_new_position)

        timeout = self._get_timeout_for_moving_to_position("FRONTDETZ", fd_new_position)
        self.ca.assert_that_pv_is("FRONTDETZ", fd_new_position, timeout=timeout)

    def test_GIVEN_front_detector_moves_towards_front_baffle_WHEN_setpoint_interval_smaller_than_threshold_THEN_motor_stops(self):
        fd_new_position = self.ca.get_pv_value("FRONTBAFFLEZ") - FD_FB_MINIMUM_INTERVAL + 50
        self.ca.set_pv_value("FRONTDETZ:SP", fd_new_position)

        self.ca.assert_that_pv_is("FRONTDETZ:MTR.MOVN", 1, timeout=1)
        self.ca.assert_that_pv_is("FRONTDETZ:MTR.TDIR", 1, timeout=1)

        timeout = self._get_timeout_for_moving_to_position("FRONTDETZ", fd_new_position)
        assert_axis_not_moving("FRONTDETZ", timeout=timeout)
        self.ca.assert_that_pv_is_not("FRONTDETZ", fd_new_position, timeout=timeout)

    def test_GIVEN_front_detector_within_threhsold_distance_to_front_baffle_WHEN_set_to_move_away_THEN_motor_not_stopped(self):
        fd_new_position = self.ca.get_pv_value("FRONTBAFFLEZ") - FD_FB_MINIMUM_INTERVAL + 50
        self.ca.set_pv_value("FRONTDETZ:SP", fd_new_position)

        self.ca.assert_that_pv_is("FRONTDETZ:MTR.MOVN", 1, timeout=1)
        self.ca.assert_that_pv_is("FRONTDETZ:MTR.TDIR", 1, timeout=1)

        timeout = self._get_timeout_for_moving_to_position("FRONTDETZ", fd_new_position)
        assert_axis_not_moving("FRONTDETZ", timeout=timeout)
        self.ca.assert_that_pv_is_not("FRONTDETZ", fd_new_position, timeout=timeout)

        fd_new_position = self.ca.get_pv_value("FRONTDETZ") - 200
        self.ca.set_pv_value("FRONTDETZ:SP", fd_new_position)

        assert_axis_moving("FRONTDETZ", timeout=1)
        self.ca.assert_that_pv_is("FRONTDETZ:MTR.TDIR", 0, timeout=1)
        timeout = self._get_timeout_for_moving_to_position("FRONTDETZ", fd_new_position)
        self.ca.assert_that_pv_is("FRONTDETZ", fd_new_position, timeout=timeout)

    def _get_axis_default_position(self, axis):
        if axis == "FRONTDETZ":
            new_position = 400
        elif axis == "FRONTBAFFLEZ":
            new_position = 1000
        elif axis == "REARBAFFLEZ":
            new_position = 1600
        elif axis == "REARDETZ":
            new_position = 2200
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

        return total_time + 1
