import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from genie_python.genie_cachannel_wrapper import WriteAccessException
import os
from parameterized.parameterized import parameterized
from utils.testing import parameterized_list, ManagerMode

# IP address of device
from utils.test_modes import TestModes

GALIL_ADDR = "128.0.0.0"

test_path = os.path.realpath(os.path.join(os.getenv("EPICS_KIT_ROOT"),
                                          "support", "motorExtensions", "master", "settings", "polaris_jaws"))

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

IOCS.append(
        {
            "name": "INSTETC",
            "directory": get_default_ioc_dir("INSTETC")
        })

TEST_MODES = [TestModes.RECSIM]
UNDERLYING_GAP_SP = "MOT:JAWS{}:{}GAP:SP"
SAMPLE_SP = "POLJAWSET:{}GAP:SP"

SET_JAW_5 = "POLJAWSET:JAWS5:SET"
TOP_LEVEL_JAW_5 = "POLJAWSET:JAWS5:{}GAP"


class JawsManagerTests(unittest.TestCase):
    """
    Tests for the Jaws Manager.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("GALIL_01")
        [ChannelAccess().assert_that_pv_exists("MOT:MTR0{}01".format(i), timeout=30) for i in range(1, 4)]
        [ChannelAccess().assert_that_pv_exists(UNDERLYING_GAP_SP.format(jaw, "V"), timeout=30) for jaw in range(1, 6)]
        self.ca = ChannelAccess()
        self.ca.assert_that_pv_exists(SAMPLE_SP.format("V"), timeout=30)
        with ManagerMode(self.ca):
            [self.ca.set_pv_value(TOP_LEVEL_JAW_5.format(direction), 0) for direction in ["V", "H"]]
            self.ca.set_pv_value(SET_JAW_5, 1)

    @parameterized.expand(parameterized_list([
        # Values tested experimentally
        ("V", 10, [52, 35.5, 26.3, 22.7], 14.6),
        ("H", 10, [53.7, 36.6, 27, 23.2], 14.8),
        ("V", 20, [55.9, 41.9, 34, 30.9], 24),
        ("H", 20, [57.6, 42.9, 34.6, 31.4], 24.1),
    ]))
    def test_GIVEN_zero_moderator_gap_WHEN_sample_gap_set_THEN_other_jaws_as_expected(self, _, direction, sample_gap, expected, expected_5):
        self.ca.set_pv_value(SAMPLE_SP.format(direction), sample_gap)
        for i, exp in enumerate(expected):
            self.ca.assert_that_pv_is_number(UNDERLYING_GAP_SP.format(i + 1, direction), exp, 0.1)
        self.ca.assert_that_pv_is_number(TOP_LEVEL_JAW_5.format(direction), expected_5, 0.1)

    @parameterized.expand(["V", "H"])
    def test_GIVEN_not_in_manager_mode_WHEN_jawset_5_written_to_THEN_exception_raised(self, direction):
        self.assertRaises(WriteAccessException, self.ca.set_pv_value, UNDERLYING_GAP_SP.format(5, direction), 10)

    @parameterized.expand(["V", "H"])
    def test_WHEN_centre_is_changed_THEN_centres_of_all_jaws_follow_and_gaps_unchanged(self, direction):
        expected_gaps = [self.ca.get_pv_value(UNDERLYING_GAP_SP.format(jaw, direction)) for jaw in range(1, 5)]

        self.ca.set_pv_value("POLJAWSET:{}CENT:SP".format(direction), 10)
        for jaw in range(1, 5):
            self.ca.assert_that_pv_is_number("MOT:JAWS{}:{}CENT:SP".format(jaw, direction), 10, 0.1)
            self.ca.assert_that_pv_is_number(UNDERLYING_GAP_SP.format(jaw, direction), expected_gaps[jaw - 1], 0.1)

    @parameterized.expand(["V", "H"])
    def test_WHEN_jaw_5_readback_changed_THEN_underlying_jaw_5_not_changed(self, direction):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        self.ca.assert_that_pv_is_number(underlying_jaw, 0)
        self.ca.assert_that_pv_is_number(TOP_LEVEL_JAW_5.format(direction), 0)

        self.ca.set_pv_value(SAMPLE_SP.format(direction), 10)
        self.ca.assert_that_pv_is_number(underlying_jaw, 0)  # Underlying jaw not changed
        self.ca.assert_that_pv_is_not_number(TOP_LEVEL_JAW_5.format(direction), 0, 5)  # Readback has changed

    @parameterized.expand(["V", "H"])
    def test_WHEN_jaw_5_set_directly_THEN_underlying_jaw_5_not_changed(self, direction):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        with ManagerMode(self.ca):
            self.ca.set_pv_value(TOP_LEVEL_JAW_5.format(direction), 10)
            self.ca.assert_that_pv_is_number(underlying_jaw, 0)

    @parameterized.expand(["V", "H"])
    def test_GIVEN_jaw_5_set_directly_WHEN_set_pv_called_THEN_underlying_jaw_5_changes(self, direction):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        with ManagerMode(self.ca):
            self.ca.set_pv_value(TOP_LEVEL_JAW_5.format(direction), 10)
            self.ca.set_pv_value(SET_JAW_5, 1)
            self.ca.assert_that_pv_is_number(underlying_jaw, 10)

    @parameterized.expand(["V", "H"])
    def test_GIVEN_jaw_5_readback_changed_WHEN_set_pv_called_THEN_underlying_jaw_5_changes(self, direction):
        underlying_jaw = UNDERLYING_GAP_SP.format(5, direction)
        self.ca.set_pv_value(SAMPLE_SP.format(direction), 10)
        with ManagerMode(self.ca):
            self.ca.set_pv_value(SET_JAW_5, 1)
            self.ca.assert_that_pv_is_number(underlying_jaw, self.ca.get_pv_value(TOP_LEVEL_JAW_5.format(direction)))

    # def test_sleep(self):
    #     from time import sleep
    #     sleep(100000)