import unittest

from utils.ioc_launcher import get_default_ioc_dir
import os
from parameterized.parameterized import parameterized
from utils.testing import parameterized_list, unstable_test
from common_tests.jaws_manager_utils import JawsManagerBase, MOD_GAP

# IP address of device
from utils.test_modes import TestModes

GALIL_ADDR = "127.0.0.11"

test_path = os.path.realpath(
    os.path.join(
        os.getenv("EPICS_KIT_ROOT"),
        "support",
        "motorExtensions",
        "master",
        "settings",
        "jaws_manager",
    )
)

# Create Galil
IOCS = [
    {
        "name": "GALIL_01",
        "directory": get_default_ioc_dir("GALIL"),
        "custom_prefix": "MOT",
        "pv_for_existence": "MTR0101",
        "macros": {
            "GALILADDR": GALIL_ADDR,
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    }
]

TEST_MODES = [TestModes.RECSIM]


class JawsManagerTests(JawsManagerBase, unittest.TestCase):
    """
    Tests for the Jaws Manager.
    """

    def get_sample_pv(self):
        return "SAMPLE"

    def get_num_of_jaws(self):
        return 2

    @parameterized.expand(
        parameterized_list(
            [
                (10, 10, [10, 10]),
                (20, 20, [20, 20]),
                (10, 0, [8, 5]),
                (20, 0, [16, 10]),
                (10, 5, [9, 7.5]),
                (20, 5, [17, 12.5]),
            ]
        )
    )
    @unstable_test()
    def test_WHEN_sample_gap_set_THEN_other_jaws_as_expected(
        self, _, mod_gap, sample_gap, expected
    ):
        self.ca.set_pv_value(MOD_GAP.format("V"), mod_gap)
        self._test_WHEN_sample_gap_set_THEN_other_jaws_as_expected("V", sample_gap, expected)

    @parameterized.expand(["V", "H"])
    def test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(
        self, direction
    ):
        self._test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(
            direction
        )

    @parameterized.expand(["V", "H"])
    def test_WHEN_sizes_at_moderator_and_sample_changed_THEN_centres_of_all_jaws_unchanged(
        self, direction
    ):
        self._test_WHEN_sizes_at_moderator_and_sample_changed_THEN_centres_of_all_jaws_unchanged(
            direction
        )
