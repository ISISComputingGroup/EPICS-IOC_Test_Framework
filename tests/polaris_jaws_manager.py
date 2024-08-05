import os
import unittest
from time import sleep

from genie_python.genie_cachannel_wrapper import WriteAccessException
from parameterized.parameterized import parameterized

from common_tests.jaws_manager_utils import UNDERLYING_GAP_SP, JawsManagerBase
from utils.ioc_launcher import get_default_ioc_dir

# IP address of device
from utils.test_modes import TestModes
from utils.testing import ManagerMode, parameterized_list, unstable_test

GALIL_ADDR = "127.0.0.11"

test_path = os.path.realpath(
    os.path.join(
        os.getenv("EPICS_KIT_ROOT"),
        "support",
        "motorExtensions",
        "master",
        "settings",
        "polaris_jaws",
    )
)

# Create 3 Galils
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
        },
    }
    for i in range(1, 4)
]

IOCS.append(
    {
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    }
)

TEST_MODES = [TestModes.RECSIM]
SAMPLE_SP = "POLJAWSET:{}GAP:SP"

JAW_5_PREFIX = "POLJAWSET:JAWS5:"
SET_JAW_5 = JAW_5_PREFIX + "SET"
TOP_LEVEL_JAW_5_GAP = JAW_5_PREFIX + "{}GAP"
TOP_LEVEL_JAW_5_CENT = JAW_5_PREFIX + "{}CENT"


class PolarisJawsManagerTests(JawsManagerBase, unittest.TestCase):
    """
    Tests for the Jaws Manager on Polaris.
    """

    def setUp(self):
        super(PolarisJawsManagerTests, self).setUp()
        with ManagerMode(self.ca):
            # Use a retry loop here in case the IOC has not connected to the manager mode PV yet
            for _ in range(10):
                try:
                    [
                        self.ca.set_pv_value(TOP_LEVEL_JAW_5_GAP.format(direction), 0)
                        for direction in ["V", "H"]
                    ]
                    self.ca.set_pv_value(SET_JAW_5, 1)
                except WriteAccessException:
                    sleep(5)
                else:
                    break
            else:
                raise WriteAccessException("Unable to write to jaws 5 in setup after 10 attempts")

    def get_sample_pv(self):
        return "POLJAWSET"

    def get_num_of_jaws(self):
        return 4

    @parameterized.expand(
        parameterized_list(
            [
                # Values gained experimentally
                ("V", 10, [52, 35.5, 26.3, 22.7], 14.6),
                ("H", 10, [53.7, 36.6, 27, 23.2], 14.8),
                ("V", 20, [55.9, 41.9, 34, 30.9], 24),
                ("H", 20, [57.6, 42.9, 34.6, 31.4], 24.1),
            ]
        )
    )
    def test_WHEN_sample_gap_set_THEN_other_jaws_as_expected(
        self, _, direction, sample_gap, expected, expected_5
    ):
        self._test_WHEN_sample_gap_set_THEN_other_jaws_as_expected(direction, sample_gap, expected)
        self.ca.assert_that_pv_is_number(TOP_LEVEL_JAW_5_GAP.format(direction), expected_5, 0.1)

    @parameterized.expand(["V", "H"])
    def test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(
        self, direction
    ):
        expected_5_gap = self.ca.get_pv_value(TOP_LEVEL_JAW_5_GAP.format(direction))
        self._test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(
            direction
        )
        self.ca.assert_that_pv_is_number(TOP_LEVEL_JAW_5_CENT.format(direction), 10, 0.1)
        self.ca.assert_that_pv_is_number(TOP_LEVEL_JAW_5_GAP.format(direction), expected_5_gap, 0.1)

    @parameterized.expand(["V", "H"])
    def test_GIVEN_not_in_manager_mode_WHEN_jawset_5_written_to_THEN_exception_raised(
        self, direction
    ):
        self.assertRaises(
            WriteAccessException, self.ca.set_pv_value, UNDERLYING_GAP_SP.format(5, direction), 10
        )

    @parameterized.expand(["V", "H"])
    def test_WHEN_jaw_5_readback_changed_THEN_underlying_jaw_5_not_changed(self, direction):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        self.ca.assert_that_pv_is_number(underlying_jaw, 0)
        self.ca.assert_that_pv_is_number(TOP_LEVEL_JAW_5_GAP.format(direction), 0)

        self.ca.set_pv_value(SAMPLE_SP.format(direction), 10)
        self.ca.assert_that_pv_is_number(underlying_jaw, 0)  # Underlying jaw not changed
        self.ca.assert_that_pv_is_not_number(
            TOP_LEVEL_JAW_5_GAP.format(direction), 0, 5
        )  # Readback has changed

    @parameterized.expand(["V", "H"])
    @unstable_test(error_class=(AssertionError, WriteAccessException), wait_between_runs=10)
    def test_WHEN_jaw_5_set_directly_THEN_underlying_jaw_5_not_changed(self, direction):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        with ManagerMode(self.ca):
            self.ca.set_pv_value(TOP_LEVEL_JAW_5_GAP.format(direction), 10)
            self.ca.assert_that_pv_is_number(underlying_jaw, 0)

    @parameterized.expand(["V", "H"])
    @unstable_test(error_class=(AssertionError, WriteAccessException), wait_between_runs=10)
    def test_GIVEN_jaw_5_set_directly_WHEN_set_pv_called_THEN_underlying_jaw_5_changes(
        self, direction
    ):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        with ManagerMode(self.ca):
            self.ca.set_pv_value(TOP_LEVEL_JAW_5_GAP.format(direction), 10)
            self.ca.set_pv_value(SET_JAW_5, 1)
            self.ca.assert_that_pv_is_number(underlying_jaw, 10)

    @parameterized.expand(["V", "H"])
    @unstable_test(error_class=(AssertionError, WriteAccessException), wait_between_runs=10)
    def test_GIVEN_jaw_5_readback_changed_WHEN_set_pv_called_THEN_underlying_jaw_5_changes(
        self, direction
    ):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        self.ca.set_pv_value(SAMPLE_SP.format(direction), 10)
        with ManagerMode(self.ca):
            self.ca.set_pv_value(SET_JAW_5, 1)
            self.ca.assert_that_pv_is_number(
                underlying_jaw, self.ca.get_pv_value(TOP_LEVEL_JAW_5_GAP.format(direction))
            )
