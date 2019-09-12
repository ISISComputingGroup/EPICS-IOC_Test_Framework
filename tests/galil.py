import unittest
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list, ManagerMode
from parameterized import parameterized

MTR_01 = "GALIL_01"


# Tests will fail if JAWS support module is not up to date and built
test_config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config"))

IOCS = [
    {
        "name": MTR_01,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
    },
    {
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC")
    }
]

TEST_MODES = [TestModes.DEVSIM]


class GalilTests(unittest.TestCase):

    """
    Tests for galil motors
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("jaws")
        self.ca = ChannelAccess(default_timeout=30)

    @parameterized.expand(["Variable", "Frozen"])
    def test_GIVEN_ioc_started_WHEN_set_position_to_THEN_motor_position_set(self, expected_frozen_offset):
        expected_postion = 100
        expected_offset = 0
        self.ca.set_pv_value("MOT:MTR0101.OFF", expected_offset)
        self.ca.set_pv_value("MOT:MTR0101.FOFF", expected_frozen_offset)
        self.ca.set_pv_value("MOT:MTR0101", 0)
        self.ca.assert_that_pv_is("MOT:MTR0101", 0, timeout=120)
        self.ca.assert_that_pv_is("MOT:MTR0101.RBV", 0)

        with ManagerMode(self.ca):
            self.ca.set_pv_value("MOT:MTR0101_SET_POSITION_IN_CONTROLLER", expected_postion)

        # set short timeout so that ensure motor doesn't actually move
        #  we do expected dmov to go 1,0,1
        self.ca.assert_that_pv_is("MOT:MTR0101", expected_postion, timeout=1)
        self.ca.assert_that_pv_is("MOT:MTR0101.RBV", expected_postion, timeout=1)

        self.ca.assert_that_pv_is("MOT:MTR0101.OFF", expected_offset)
        self.ca.assert_that_pv_is("MOT:MTR0101.SET", "Use")
        self.ca.assert_that_pv_is("MOT:MTR0101.FOFF", expected_frozen_offset)
