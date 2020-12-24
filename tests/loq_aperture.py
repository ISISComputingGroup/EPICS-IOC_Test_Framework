import unittest
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from parameterized import parameterized
from collections import OrderedDict

# Internal Address of device (must be 2 characters)
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"

PREFIX = "MOT"

# Motor position tolerance
TOLERANCE = 2e-1

# PV names for X/Y motors
MOTOR = "MOT:MTR0101"

# Axis position index PV and SP
POSITION_INDEX = "LKUP:APERTURE:NIPOSN"
POSITION_SP = "LKUP:APERTURE:IPOSN:SP"

# PV reading closest beamstop position
CLOSESTSHUTTER = "APERTURE:CLOSESTSHUTTER"

# PV which sends the motor to closest beamstop motion set point
CLOSEAPERTURE = "APERTURE:CLOSEAPERTURE"

# Test motion set points located in test_support/loq_aperture.
MOTION_SETPOINT = OrderedDict([("Aperture_large",  02.900000),
                               ("Stop_01",         15.400000),
                               ("Aperture_medium", 27.900000),
                               ("Stop_02",         40.400000),
                               ("Aperture_small",  52.900000)])

SETPOINT_GAP = MOTION_SETPOINT["Stop_01"] - MOTION_SETPOINT["Aperture_large"]

test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motorExtensions", "master", "settings", "loqAperture"))

IOCS = [
    {
        "name": "GALIL_01",
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "1",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
            "ICPCONFIGROOT": test_path.replace("\\", "/"),
        },
    },
]


TEST_MODES = [TestModes.DEVSIM]


class LoqApertureTests(unittest.TestCase):
    """
    Tests for the LOQ Aperture
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.assert_that_pv_exists(MOTOR, timeout=60)
        self.ca.assert_that_pv_exists(CLOSESTSHUTTER)
        self.ca.assert_that_pv_exists(CLOSEAPERTURE)

    # Closest positions defined in ticket 3623
    @parameterized.expand([
        ("Aperture_large",  0, 1),
        ("Stop_01",         1, 1),
        ("Aperture_medium", 2, 3),
        ("Stop_02",         3, 3),
        ("Aperture_small",  4, 3),
    ])
    def test_GIVEN_motor_on_an_aperture_position_WHEN_motor_set_to_closest_beamstop_THEN_motor_moves_to_closest_beamstop(self, start_position, start_index, closest_stop):
        # GIVEN
        self.ca.set_pv_value(POSITION_SP, start_index)
        self.ca.assert_that_pv_is_number(POSITION_INDEX, start_index, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number(MOTOR, MOTION_SETPOINT[start_position], tolerance=TOLERANCE)

        # WHEN
        self.ca.process_pv(CLOSEAPERTURE)

        # THEN
        self.ca.assert_that_pv_is_number(CLOSESTSHUTTER, closest_stop)
        self.ca.assert_that_pv_is_number(POSITION_INDEX, closest_stop, timeout=5)
        self.ca.assert_that_pv_is_number(MOTOR, list(MOTION_SETPOINT.values())[closest_stop], tolerance=TOLERANCE)

    # Closest positions defined in ticket 3623
    @parameterized.expand([
        ("Aperture_large",  0, 1),
        ("Stop_01",         1, 1),
        ("Aperture_medium", 2, 3),
        ("Stop_02",         3, 3),
        ("Aperture_small",  4, 3),
    ])
    def test_GIVEN_motor_off_setpoint_WHEN_motor_set_to_closest_beamstop_THEN_motor_moves_to_closest_beamstop(self, _, start_index, closest_stop):
        # GIVEN
        # Move 25 per cent forwards and backwards off centre of setpoint
        for fraction_moved_off_setpoint in [0.25, -0.25]:
            initial_position = list(MOTION_SETPOINT.values())[start_index] + (fraction_moved_off_setpoint * SETPOINT_GAP)
            self.ca.set_pv_value(MOTOR, initial_position)
            self.ca.assert_that_pv_is_number(MOTOR, initial_position, tolerance=TOLERANCE)

            # This assertion ensures that this calc record has updated with the closest beam stop position
            self.ca.assert_that_pv_is_number(CLOSESTSHUTTER, closest_stop)

            # WHEN
            self.ca.process_pv(CLOSEAPERTURE)

            # THEN
            self.ca.assert_that_pv_is_number(CLOSESTSHUTTER, closest_stop)
            self.ca.assert_that_pv_is_number(POSITION_INDEX, closest_stop, timeout=5)
            self.ca.assert_that_pv_is_number(MOTOR, list(MOTION_SETPOINT.values())[closest_stop], tolerance=TOLERANCE)
