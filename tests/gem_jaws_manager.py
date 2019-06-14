import unittest

from utils.ioc_launcher import get_default_ioc_dir
import os
from parameterized.parameterized import parameterized
from utils.testing import parameterized_list
from common_tests.jaws_manager_utils import JawsManagerBase, MOD_GAP
from time import sleep

# IP address of device
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"

test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motorExtensions", "master", "settings", "gem_jaws"))

# Create 3 Galils
IOCS = [{
            "name": "GALIL_0{}".format(i),
            "directory": get_default_ioc_dir("GALIL", i),
            "pv_for_existence": "AXIS1",
            "macros": {
                "GALILADDR": GALIL_ADDR,
                "MTRCTRL": "0{}".format(i),
                "GALILCONFIGDIR": test_path.replace("\\", "/"),
            }
           } for i in range(1, 4)]

TEST_MODES = [TestModes.RECSIM]


class GemJawsManagerTests(JawsManagerBase, unittest.TestCase):
    """
    Tests for the Jaws Manager on Gem.
    """
    def get_num_of_jaws(self):
        return 5

    # def get_sample_pv(self):
    #     return "GEMJAWSET:SAMPLE"

    @parameterized.expand(parameterized_list([
        # Numbers taken experimentally
        (30, 10, [22.6, 20.4, 17.9, 15.1, 11.9]),
        (130, 5, [83.6, 70.2, 54, 37, 16.9]),
        (100, 50, [81.4, 76.1, 69.6, 62.8, 54.7]),
    ]))
    def test_WHEN_sample_gap_set_THEN_other_jaws_as_expected(self, _, mod_gap, sample_gap, expected):
        self.ca.set_pv_value(MOD_GAP.format("V"), mod_gap)
        sleep(1)  # Setting moderator and sample in quick succession causes issues
        self._test_WHEN_sample_gap_set_THEN_other_jaws_as_expected("V", sample_gap, expected)
