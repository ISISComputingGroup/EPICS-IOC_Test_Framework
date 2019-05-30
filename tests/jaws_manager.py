import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from genie_python.genie_cachannel_wrapper import WriteAccessException
import os
from parameterized.parameterized import parameterized
from utils.testing import parameterized_list, ManagerMode
from common_tests.jaws_manager_utils import JawsManagerBase

# IP address of device
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"

test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motorExtensions", "master", "settings", "jaws_manager"))

# Create Galil
IOCS = [{
            "name": "GALIL_01",
            "directory": get_default_ioc_dir("GALIL"),
            "pv_for_existence": "AXIS1",
            "macros": {
                "GALILADDR": GALIL_ADDR,
                "MTRCTRL": "01",
                "GALILCONFIGDIR": test_path.replace("\\", "/"),
            }
        }]

TEST_MODES = [TestModes.RECSIM]


class JawsManagerTests(JawsManagerBase, unittest.TestCase):
    """
    Tests for the Jaws Manager.
    """
    def get_sample_pv(self):
        return "SAMPLE"

    def get_num_of_jaws(self):
        return 2

    @parameterized.expand(parameterized_list([
        ("V", 10, [10, 10]),
        ("H", 20, [20, 20]),
        ("V", 0, [8, 5]),
        ("H", 0, [16, 10]),
        ("V", 5, [9, 7.5]),
        ("H", 5, [17, 12.5]),
    ]))
    def test_WHEN_sample_gap_set_THEN_other_jaws_as_expected(self, _, direction, sample_gap, expected):
        self._test_WHEN_sample_gap_set_THEN_other_jaws_as_expected(direction, sample_gap, expected)

    @parameterized.expand(["V", "H"])
    def test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(self, direction):
        self._test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(direction)
