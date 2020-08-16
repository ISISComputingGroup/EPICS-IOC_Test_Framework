import unittest
import os
from parameterized import parameterized

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.axis import set_axis_moving, assert_axis_moving, assert_axis_not_moving
from utils.testing import parameterized_list
from time import sleep

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

TEST_MODES = [TestModes.RECSIM]

AXES_TO_STOP = [
    "FRONTDETZ", "FRONTDETX", "FRONTDETROT", "REARDETZ", "REARDETX", "REARBAFFLEZ", "FRONTBAFFLEZ",
    "BEAMSTOPX", "BEAMSTOP2Y", "BEAMSTOP1Y", "BEAMSTOP3Y", "FRONTBEAMSTOP",
    "JAWRIGHT", "JAWLEFT", "JAWUP", "JAWDOWN", "FRONTSTRIP", "REARSTRIP"
]

INTERVAL_PAIRS = [("FRONTDETZ", "FRONTBAFFLEZ"), ("FRONTBAFFLEZ", "REARBAFFLEZ"), ("REARBAFFLEZ", "REARDETZ"), ]

INTERVAL_SETPOINT_PAIRS = [("FRONTDETZ:SP", "FRONTBAFFLEZ:SP"), ("FRONTBAFFLEZ:SP", "REARBAFFLEZ:SP"),
                           ("REARBAFFLEZ:SP", "REARDETZ:SP")]

BAFFLE_AND_DETECTORS_INTERVAL_NAMES = ["FDFB", "FBRB", "RBRD"]

BAFFLE_AND_DETECTORS_INTERVAL_SETPOINT_NAMES = ["FDSPFBSP", "FBSPRBSP", "RBSPRDSP"]

BAFFLES_AND_DETECTORS_Z_AXES = ["FRONTDETZ", "FRONTBAFFLEZ", "REARBAFFLEZ", "REARDETZ"]

MAJOR_ALARM_INTERVAL_THRESHOLD = 50
MINOR_ALARM_INTERVAL_THRESHOLD = 100


class Sans2dVacTankTests(unittest.TestCase):
    """
    Tests for the sans2d vacuum tank motor extensions.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix="MOT")

    # @parameterized.expand(AXES_TO_STOP)
    # def test_GIVEN_axis_moving_WHEN_stop_all_THEN_axis_stopped(self, axis):
    #     for _ in range(3):
    #         set_axis_moving(axis)
    #         assert_axis_moving(axis)
    #         self.ca.set_pv_value("SANS2DVAC:STOP_MOTORS:ALL", 1)
    #         assert_axis_not_moving(axis)

    @parameterized.expand(parameterized_list(zip(INTERVAL_PAIRS, BAFFLE_AND_DETECTORS_INTERVAL_NAMES)))
    def test_GIVEN_motor_interval_above_minor_warning_threshold_THEN_interval_is_correct_and_not_in_alarm(self, _, z_axes_pair, interval_name):
        self._setup_vac_tank_detectors_and_baffles()
        z_axis_a, z_axis_b = z_axes_pair

        b_position = self.ca.get_pv_value(z_axis_b)
        a_new_position = b_position - 50 - MINOR_ALARM_INTERVAL_THRESHOLD
        expected_interval = b_position - a_new_position

        self.ca.set_pv_value("{}:SP".format(z_axis_a), a_new_position)

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=15)
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

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=15)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(zip(INTERVAL_PAIRS, BAFFLE_AND_DETECTORS_INTERVAL_NAMES)))
    def test_GIVEN_motor_interval_under_minor_warning_threshold_THEN_interval_is_correct_and_in_minor_alarm(self, _, z_axes_pair, interval_name):
        self._setup_vac_tank_detectors_and_baffles()
        z_axis_a, z_axis_b = z_axes_pair

        b_position = self.ca.get_pv_value(z_axis_b)
        a_new_position = b_position - MINOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = b_position - a_new_position

        self.ca.set_pv_value("{}:SP".format(z_axis_a), a_new_position)

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=15)
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

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=15)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list(zip(INTERVAL_PAIRS, BAFFLE_AND_DETECTORS_INTERVAL_NAMES)))
    def test_GIVEN_motor_interval_under_major_warning_threshold_THEN_interval_is_correct_and_in_major_alarm(self, _, z_axes_pair, interval_name):
        self._setup_vac_tank_detectors_and_baffles()
        z_axis_a, z_axis_b = z_axes_pair

        b_position = self.ca.get_pv_value(z_axis_b)
        a_new_position = b_position - MAJOR_ALARM_INTERVAL_THRESHOLD + 1
        expected_interval = b_position - a_new_position

        self.ca.set_pv_value("{}:SP".format(z_axis_a), a_new_position)

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=15)
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

        self.ca.assert_that_pv_is("SANS2DVAC:{}:INTERVAL".format(interval_name), expected_interval, timeout=15)
        self.ca.assert_that_pv_alarm_is("SANS2DVAC:{}:INTERVAL".format(interval_name), self.ca.Alarms.MAJOR)

    def _setup_vac_tank_detectors_and_baffles(self):
        for axis in BAFFLES_AND_DETECTORS_Z_AXES:
            current_position = self.ca.get_pv_value(axis)

            new_position = self._get_axis_default_position(axis)

            if current_position != new_position:
                self.ca.set_pv_value("{}:MTR.VMAX".format(axis), 200)
                self.ca.set_pv_value("{}:MTR.VELO".format(axis), 200)
                self.ca.set_pv_value("{}:MTR.ACCL".format(axis), 1)

                self.ca.set_pv_value("{}:SP".format(axis), new_position)

        for axis in BAFFLES_AND_DETECTORS_Z_AXES:
            new_position = self._get_axis_default_position(axis)
            self.ca.assert_that_pv_is(axis, new_position, timeout=20)

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
