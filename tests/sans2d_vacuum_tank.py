import time
import unittest
import os

from genie_python.channel_access_exceptions import WriteAccessException
from parameterized import parameterized

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.axis import set_axis_moving, assert_axis_moving, assert_axis_not_moving, stop_axis_moving
from utils.testing import ManagerMode

test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "motorExtensions", "master", "settings", "sans2d_vacuum_tank")
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

AXES_TO_STOP = [
    "FRONTDETZ", "FRONTDETX", "FRONTDETROT", "REARDETZ", "REARDETX", "REARBAFFLEZ", "FRONTBAFFLEZ",
    "BEAMSTOPX", "BEAMSTOP2Y", "BEAMSTOP1Y", "BEAMSTOP3Y", "FRONTBEAMSTOP",
    "JAWRIGHT", "JAWLEFT", "JAWUP", "JAWDOWN", "FRONTSTRIP", "REARSTRIP"
]


class Sans2dVacTankTests(unittest.TestCase):
    """
    Tests for the sans2d vacuum tank motor extensions.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix="MOT")
        self.lower_inhibit_bound = -2
        self.upper_inhibit_bound = 2

    def reset_axis_to_non_inhibit(self, axis):
        self.ca.set_pv_value("{}:SP".format(axis), 0)
        self.ca.assert_that_pv_is_number(axis, 0, tolerance=1.9, timeout=10)
        self.ca.set_pv_value("{}:MTR.STOP".format(axis), 1, wait=True)

    def reset_axes_to_non_inhibit(self, axis_one, axis_two):
        axis_one_val = self.ca.get_pv_value(axis_one)
        axis_two_val = self.ca.get_pv_value(axis_two)
        axis_one_inhibiting = axis_one_val < self.lower_inhibit_bound or axis_one_val > self.upper_inhibit_bound
        axis_two_inhibiting = axis_two_val < self.lower_inhibit_bound or axis_two_val > self.upper_inhibit_bound
        if axis_one_inhibiting and axis_two_inhibiting:
            self.fail("Both {} and {} are inhibiting each other, cannot reliably run test".format(axis_one, axis_two))
        elif axis_one_inhibiting:
            self.reset_axis_to_non_inhibit(axis_one)
        elif axis_two_inhibiting:
            self.reset_axis_to_non_inhibit(axis_two)

    def _set_collision_avoidance_state_with_retries(self, state):
        with ManagerMode(ChannelAccess()):
            for _ in range(5):
                try:
                    self.ca.set_pv_value("SANS2DVAC:COLLISION_AVOIDANCE", state)
                    break
                except WriteAccessException as e:
                    err = e
                    time.sleep(1)
            else:
                raise err

    @parameterized.expand(AXES_TO_STOP)
    def test_GIVEN_axis_moving_WHEN_stop_all_THEN_axis_stopped(self, axis):
        self._set_collision_avoidance_state_with_retries(1)

        for _ in range(3):
            set_axis_moving(axis)
            assert_axis_moving(axis)
            self.ca.set_pv_value("SANS2DVAC:STOP_MOTORS:ALL", 1)
            assert_axis_not_moving(axis)
        self.reset_axis_to_non_inhibit(axis)

        self._set_collision_avoidance_state_with_retries(0)

    @parameterized.expand([("FRONTBEAMSTOP", "FRONTDETROT"), ("FRONTDETROT", "FRONTBEAMSTOP")])
    def test_GIVEN_axes_in_range_WHEN_axis_goes_out_of_range_THEN_other_axis_inhibited(self, inhibiting_axis, inhibited_axis):
        # Arrange
        self.reset_axes_to_non_inhibit(inhibited_axis, inhibiting_axis)
        try:
            # Act
            self.ca.set_pv_value("{}:SP".format(inhibiting_axis), -3, wait=True)
            self.ca.assert_that_pv_is_number("{}:SP".format(inhibiting_axis), -3)
            start_position = self.ca.get_pv_value(inhibited_axis)
            with self.assertRaises(WriteAccessException, msg="DISP should be set on inhibited axis"):
                set_axis_moving(inhibited_axis)
            # Assert
            self.ca.assert_that_pv_is("SANS2DVAC:INHIBIT_{}".format(inhibited_axis), 1)
            end_position = self.ca.get_pv_value(inhibited_axis)
            self.assertEqual(start_position, end_position)
        finally:
            # Rearrange
            self.reset_axes_to_non_inhibit(inhibited_axis, inhibiting_axis)

