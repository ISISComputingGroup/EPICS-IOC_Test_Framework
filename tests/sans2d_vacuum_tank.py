import unittest
import os
from parameterized import parameterized

from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.axis import set_axis_moving, assert_axis_moving, assert_axis_not_moving

test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "motorExtensions", "master", "settings", "sans2d")
)

GALIL_ADDR = "128.0.0.0"

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


class Sans2dVacTankTests(unittest.TestCase):
    """
    Tests for the sans2d vacuum tank motor extensions.
    """

    def setUp(self):
        self.ca = ChannelAccess(device_prefix="MOT")

    @parameterized.expand(AXES_TO_STOP)
    def test_GIVEN_axis_moving_WHEN_stop_all_THEN_axis_stopped(self, axis):
        for _ in range(3):
            set_axis_moving(axis)
            assert_axis_moving(axis)
            self.ca.set_pv_value("SANS2DVAC:STOP_MOTORS:ALL", 1)
            assert_axis_not_moving(axis, retry_count=3)
