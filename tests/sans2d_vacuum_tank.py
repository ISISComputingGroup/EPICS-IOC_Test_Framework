import os
import unittest

from genie_python.channel_access_exceptions import WriteAccessException
from parameterized import parameterized

from utils.axis import set_axis_moving
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP, IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list

test_path = os.path.realpath(
    os.path.join(
        os.getenv("EPICS_KIT_ROOT"),
        "support",
        "motorExtensions",
        "master",
        "settings",
        "sans2d_vacuum_tank",
    )
)

GALIL_ADDR1 = "127.0.0.11"
GALIL_ADDR2 = "127.0.0.12"
GALIL_ADDR3 = "127.0.0.13"

# Create GALIL_03, GALIL_04 and GALIL_05
IOCS = [
    {
        "name": "FINS_01",
        "directory": get_default_ioc_dir("FINS"),
        "custom_prefix": "FINS_VAC",
        "pv_for_existence": "HEARTBEAT",
        "macros": {
            "FINSCONFIGDIR": (
                os.path.join(EPICS_TOP, "ioc", "master", "FINS", "exampleSettings", "SANS2D_vacuum")
            ).replace("\\", "/"),
            "PLCIP": "127.0.0.1",
        },
    },
    {
        "name": "GALIL_03",
        "directory": get_default_ioc_dir("GALIL", 3),
        "custom_prefix": "MOT",
        "pv_for_existence": "MTR0301",
        "macros": {
            "GALILADDR": GALIL_ADDR1,
            "MTRCTRL": "03",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
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
        },
    },
]

# SPMG
PAUSE, MOVE, GO = 1, 2, 3


TEST_MODES = [TestModes.RECSIM]

AXES_TO_STOP = [
    "FRONTDETZ",
    "FRONTDETX",
    "FRONTDETROT",
    "REARDETZ",
    "REARDETX",
    "REARBAFFLEZ",
    "FRONTBAFFLEZ",
    "BEAMSTOPX",
    "BEAMSTOP2Y",
    "BEAMSTOP1Y",
    "BEAMSTOP3Y",
    "FRONTBEAMSTOP",
    "JAWRIGHT",
    "JAWLEFT",
    "JAWUP",
    "JAWDOWN",
    "FRONTSTRIP",
    "REARSTRIP",
]

AXES_FOR_CA = [
    "FRONTDETZ",
    "FRONTDETX",
    "FRONTDETROT",
    "REARDETZ",
    "REARDETX",
    "REARBAFFLEZ",
    "FRONTBAFFLEZ",
]


class Sans2dVacTankTests(unittest.TestCase):
    """
    Tests for the sans2d vacuum tank motor extensions (limiting the rotation in the tank).
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix="MOT")
        self.lower_inhibit_bound = -2
        self.upper_inhibit_bound = 2

    def reset_axis_to_non_inhibit(self, axis):
        self.ca.set_pv_value("{}:SP".format(axis), 0)
        self.ca.assert_that_pv_is_number(axis, 0, timeout=10)

    def reset_axes_to_non_inhibit(self, axis_one, axis_two):
        axis_one_val = self.ca.get_pv_value("{}:SP".format(axis_one))
        axis_two_val = self.ca.get_pv_value("{}:SP".format(axis_two))
        axis_one_inhibiting = (
            axis_one_val < self.lower_inhibit_bound or axis_one_val > self.upper_inhibit_bound
        )
        axis_two_inhibiting = (
            axis_two_val < self.lower_inhibit_bound or axis_two_val > self.upper_inhibit_bound
        )
        if axis_one_inhibiting and axis_two_inhibiting:
            self.fail(
                "Both {} and {} are inhibiting each other, cannot reliably run test".format(
                    axis_one, axis_two
                )
            )
        elif axis_one_inhibiting:
            self.reset_axis_to_non_inhibit(axis_one)
        elif axis_two_inhibiting:
            self.reset_axis_to_non_inhibit(axis_two)

    @parameterized.expand([("FRONTBEAMSTOP", "FRONTDETROT"), ("FRONTDETROT", "FRONTBEAMSTOP")])
    def test_GIVEN_axes_in_range_WHEN_axis_goes_out_of_range_THEN_other_axis_inhibited(
        self, inhibiting_axis, inhibited_axis
    ):
        # Arrange
        self.reset_axes_to_non_inhibit(inhibited_axis, inhibiting_axis)
        try:
            # Act
            self.ca.set_pv_value("{}:SP".format(inhibiting_axis), -3)
            self.ca.assert_that_pv_is_number("{}:SP".format(inhibiting_axis), -3)
            start_position = self.ca.get_pv_value(inhibited_axis)
            with self.assertRaises(
                WriteAccessException, msg="DISP should be set on inhibited axis"
            ):
                set_axis_moving(inhibited_axis)
            # Assert
            self.ca.assert_that_pv_is("SANS2DVAC:INHIBIT_{}".format(inhibited_axis), 1)
            end_position = self.ca.get_pv_value(inhibited_axis)
            self.assertEqual(start_position, end_position)
        finally:
            # Rearrange
            self.reset_axes_to_non_inhibit(inhibited_axis, inhibiting_axis)


class Sans2dVacuumTankTest(unittest.TestCase):
    """
    Tests for the SANS2D vacuum tank, based on a FINS PLC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("FINS_01")
        self.ca = ChannelAccess(device_prefix="FINS_VAC")

    @parameterized.expand(parameterized_list([-5, 0, 3, 5, 7, 9, 16]))
    def test_WHEN_set_tank_status_to_unknown_value_THEN_error_status(self, _, status_rval):
        self.ca.set_pv_value("SIM:TANK:STATUS", status_rval)
        self.ca.assert_that_pv_is("TANK:STATUS", "ERROR: STATUS UNKNOWN")
        self.ca.assert_that_pv_alarm_is("TANK:STATUS", "MAJOR")

    @parameterized.expand([(1, "ATMOSPHERE"), (2, "VAC DOWN"), (4, "AT VACUUM"), (8, "VENTING")])
    def test_WHEN_set_tank_status_to_known_value_THEN_no_error(self, status_rval, status_val):
        self.ca.set_pv_value("SIM:TANK:STATUS", status_rval)
        self.ca.assert_that_pv_is("TANK:STATUS", status_val)
        self.ca.assert_that_pv_alarm_is("TANK:STATUS", "NO_ALARM")
