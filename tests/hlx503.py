import unittest

from parameterized import parameterized
from itertools import product

from genie_python.utilities import dehex_and_decompress

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

# Device prefix
DEVICE_PREFIX = "HLX503_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulator": "hlx503",
        "macros": {
            "SORB_CHANNEL": 1,
            "1KPOTHE3POTLO_CHANNEL": 2,
            "HE3POTHI_CHANNEL": 3,
            "SORB_SENSOR": 1,
            "1KPOTHE3POTLO_SENSOR": 2,
            "HE3POTHI_SENSOR": 3,
            "MAX_TEMP_FOR_HE3_COOLING": 2.0,
            "MAX_OPERATING_TEMP_FOR_HELIOX": 20.0,
            "RECONDENSE_SORB_TEMP_FINAL": 20.0,
            "RECONDENSE_SORB_TEMP_SET": 33.0,
            "RECONDENSE_SORB_P": 1.2,
            "RECONDENSE_SORB_I": 1.2,
            "RECONDENSE_SORB_D": 1.2,
            "RECONDENSE_HE3POT_TARGET_TEMP_PART1": 1.5,
            "RECONDENSE_HE3POT_TARGET_TEMP_PART2": 1.6,
            "RECONDENSE_POST_PART2_WAIT_TIME": 10,
            "RECONDENSE_PART_TIMEOUT": 1800,
            "RECONDENSE_PART_TIMEOUT_ON": "YES"
        }
    },
]

channels = {
    "SORB": "SORB",
    "HE3POT": "HE3POTHI"
}

pv_to_macros_map = {
    "RE:SORB:TEMP:FIN:SP": "RECONDENSE_SORB_TEMP_FINAL",
    "RE:SORB:TEMP:SP": "RECONDENSE_SORB_TEMP_SET",
    "RE:SORB:P:SP": "RECONDENSE_SORB_P",
    "RE:SORB:I:SP": "RECONDENSE_SORB_I",
    "RE:SORB:D:SP": "RECONDENSE_SORB_D",
    "RE:HE3POT:TEMP:PART1:SP": "RECONDENSE_HE3POT_TARGET_TEMP_PART1",
    "RE:HE3POT:TEMP:PART2:SP": "RECONDENSE_HE3POT_TARGET_TEMP_PART1",
    "RE:PART2:WAIT_TIME:SP": "RECONDENSE_POST_PART2_WAIT_TIME",
    "MAX_TEMP_FOR_HE3_COOLING:SP": "MAX_TEMP_FOR_HE3_COOLING",
    "RE:TIMEOUT:SP": "RECONDENSE_PART_TIMEOUT",
    "RE:TIMEOUT:ON:SP": "RECONDENSE_PART_TIMEOUT_ON"
}


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

PID_TABLE_LOOKUP_VALUES = [
    (0.6, 10.0, 11.0, 12.0, "SORB"), (4.0, 20.0, 21.0, 22.0, "SORB"), (5.8, 30.0, 31.0, 32.0, "SORB"),
    (0.6, 13.0, 14.0, 15.0, "HE3POT"), (4.0, 23.0, 24.0, 25.0, "HE3POT"), (5.8, 33.0, 34.0, 35.0, "HE3POT")
]

UNATTAINABLE_RECONDENSE_VALUES = {
    "RE:SORB:TEMP:SP": 10000, "RE:SORB:TEMP:FIN:SP": -1000,
    "RE:HE3POT:TEMP:PART1:SP": -1, "RE:HE3POT:TEMP:PART2:SP": -1
}

PID_TEST_VALUES = [0.2, 3.8]

CONTROL_CHANNELS = ["SORB", "HE3POTHI", "1KPOTHE3POTLO"]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ITC503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("hlx503", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_run_function_on_device("backdoor_plug_in_he3potlow")

        self.reset_any_changes_from_recondense()
        self.reset_any_changes_from_macros()

    def reset_any_changes_from_recondense(self):
        self.ca.set_pv_value("RE:CANCELLED:SP", "YES")
        self.ca.set_pv_value("RE:SKIPPED:SP", "NO")
        self.ca.set_pv_value("RE:CANCELLED:SP", "NO")
        self.ca.set_pv_value("RECONDENSING:SP", "NO")
        self.ca.set_pv_value("RE:TIMED_OUT", "NO")
        self.ca.assert_that_pv_is("RECONDENSING", "NO")
        self.ca.assert_that_pv_is("RE:PART", "NOT RECONDENSING")
        self._lewis.backdoor_run_function_on_device("reset_to_temp_control_state")

    def reset_any_changes_from_macros(self):
        for pv, macro in pv_to_macros_map.items():
            self.ca.set_pv_value(pv, IOCS[0]["macros"][macro])

    def set_unattainable_recondense_conditions(self):
        for pv, value in UNATTAINABLE_RECONDENSE_VALUES.items():
            self.ca.set_pv_value(pv, value)

    @parameterized.expand(parameterized_list(["Auto", "Manual"]))
    def test_WHEN_set_autoheat_THEN_autoheat_set(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(value, "MODE:HTR")

    @parameterized.expand(parameterized_list(["ON", "OFF"]))
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_set_autopid_AND_THEN_autopid_set(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(value, "AUTOPID")

    @parameterized.expand(parameterized_list(["Locked", "Remote only", "Local only", "Local and remote"]))
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_set_ctrl_THEN_ctrl_set(self, _, value):
        expected_alarm = self.ca.Alarms.NONE if value != "Local only" else self.ca.Alarms.MAJOR
        self.ca.assert_setting_setpoint_sets_readback(value, "CTRL", expected_alarm=expected_alarm)

    @parameterized.expand(parameterized_list([2.4, 18.3]))
    def test_WHEN_temp_set_THEN_temp_sp_rbv_correct(self, _, val):
        self.ca.set_pv_value("TEMP:SP", val)
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", val, tolerance=0.1)

    @parameterized.expand(parameterized_list(CONTROL_CHANNELS))
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_ctrlchannel_set_THEN_ctrlchannel_set(self, _, new_control_channel):
        self.ca.assert_setting_setpoint_sets_readback(new_control_channel, "CTRLCHANNEL")

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    def test_WHEN_proportional_set_THEN_proportional_set(self, _, proportional):
        self.ca.assert_setting_setpoint_sets_readback(proportional, "P")

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    def test_WHEN_integral_set_THEN_integral_set(self, _, integral):
        self.ca.assert_setting_setpoint_sets_readback(integral, "I")

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    def test_WHEN_derivative_set_THEN_derivative_set(self, _, derivative):
        self.ca.assert_setting_setpoint_sets_readback(derivative, "D")

    @parameterized.expand(parameterized_list([23.2, 87.1]))
    def test_WHEN_heater_output_set_THEN_heater_output_set(self, _, heater_output):
        self.ca.assert_setting_setpoint_sets_readback(heater_output, "HEATERP")

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_set_he3pot_temp_above_he3_cooling_threshold_THEN_he3pot_high_temp_set(self):
        self._lewis.backdoor_set_on_device("he3pot_temp", 1.5)
        self.ca.set_pv_value("TEMP:HE3POT:SP", 3.0)
        self.ca.assert_that_pv_is("CTRLCHANNEL", "HE3POTHI")
        self.ca.assert_that_pv_is("TEMP:HE3POTHI", 3.0)
        self.ca.assert_that_pv_is("TEMP:HE3POT", 3.0)

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_set_he3pot_temp_below_he3_cooling_threshold_THEN_he3pot_low_temp_set(self):
        self._lewis.backdoor_set_on_device("he3pot_temp", 3.0)
        self.ca.set_pv_value("TEMP:HE3POT:SP", 1.0)
        self.ca.assert_that_pv_is("CTRLCHANNEL", "1KPOTHE3POTLO")
        self.ca.assert_that_pv_is("TEMP:1KPOTHE3POTLO", 1.0)
        self.ca.assert_that_pv_is("TEMP:HE3POT", 1.0)

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_set_he3pot_temp_above_max_temp_threshold_THEN_he3pot_temp_not_set_AND_in_alarm(self):
        he3pot_temp = self.ca.get_pv_value("TEMP:HE3POT")
        ctrl_channel = self.ca.get_pv_value("CTRLCHANNEL")
        self.ca.set_pv_value("TEMP:HE3POT:SP", 22.0)
        self.ca.assert_that_pv_alarm_is("TEMP:HE3POT:SP", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("CTRLCHANNEL", ctrl_channel)
        self.ca.assert_that_pv_is("TEMP:HE3POTHI", he3pot_temp)
        self.ca.assert_that_pv_is("TEMP:1KPOTHE3POTLO", he3pot_temp)
        self.ca.assert_that_pv_is("TEMP:HE3POT", he3pot_temp)

    def test_WHEN_turn_heater_off_THEN_heater_output_zero_AND_autoheat_off(self):
        # Arrange
        self.ca.assert_setting_setpoint_sets_readback("Auto", "MODE:HTR")
        self.ca.assert_setting_setpoint_sets_readback(10.0, "HEATERP")
        # Act
        self.ca.process_pv("HEATER:OFF")
        # Assert
        self.ca.assert_that_pv_is("HEATERP", 0.0)
        self.ca.assert_that_pv_is("MODE:HTR", "Manual")

    @skip_if_recsim("ReadASCII struggles in recsim")
    def test_WHEN_get_pid_files_THEN_pid_files_present(self):
        pid_files = dehex_and_decompress(self.ca.get_pv_value("PID_FILES"))
        self.assertTrue("SORB_file.txt" in pid_files)
        self.assertTrue("HE3POT_file.txt" in pid_files)
        self.assertTrue("Default.txt" in pid_files)

    @skip_if_recsim("ReadASCII struggles in recsim")
    def test_WHEN_set_pid_file_THEN_pid_set(self):
        self.ca.set_pv_value("HE3POT:PID_FILE:SP", "HE3POT_file.txt")
        self.ca.set_pv_value("SORB:PID_FILE:SP", "SORB_file.txt")
        self.ca.assert_that_pv_is("HE3POT:PID_FILE", "HE3POT_file.txt")
        self.ca.assert_that_pv_is("SORB:PID_FILE", "SORB_file.txt")
        self.ca.assert_that_pv_alarm_is("HE3POT:PID_FILE", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_alarm_is("SORB:PID_FILE", self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(PID_TABLE_LOOKUP_VALUES))
    @skip_if_recsim("ReadASCII struggles in recsim")
    def test_WHEN_temp_set_THEN_pids_set_correctly(self, _, temp, p, i, d, sorb_or_he3pot):
        self.ca.assert_setting_setpoint_sets_readback("YES", "ADJUST_PIDS")
        self.ca.assert_setting_setpoint_sets_readback(f"{sorb_or_he3pot}_file.txt", f"{sorb_or_he3pot}:PID_FILE")
        self.ca.set_pv_value(f"TEMP:{sorb_or_he3pot}:SP", temp)
        self.ca.assert_that_pv_is("P", p)
        self.ca.assert_that_pv_is("I", i)
        self.ca.assert_that_pv_is("D", d)

    @parameterized.expand(parameterized_list([("SORB", "HE3POT"), ("HE3POT", "SORB")]))
    @skip_if_recsim("ReadASCII struggles in recsim")
    def test_GIVEN_control_channel_WHEN_using_control_channel_THEN_correct_pid_file_used(self,
            _, pid_pv_prefix, not_in_use_pid_pv_prefix):
        self.ca.assert_setting_setpoint_sets_readback("YES", "ADJUST_PIDS")
        self.ca.set_pv_value(f"{pid_pv_prefix}:PID_FILE:SP", f"{pid_pv_prefix}_file.txt")
        self.ca.set_pv_value(f"{not_in_use_pid_pv_prefix}:PID_FILE:SP", f"{not_in_use_pid_pv_prefix}_file.txt")
        self.ca.set_pv_value("CTRLCHANNEL:SP", channels[pid_pv_prefix])
        self.ca.assert_that_pv_is("_PID_FILE", f"{pid_pv_prefix}_file.txt")

    @parameterized.expand(parameterized_list(PID_TABLE_LOOKUP_VALUES))
    @skip_if_recsim("ReadASCII struggles in recsim")
    def test_WHEN_temp_set_AND_lookup_table_off_THEN_pids_not_set(self, _, temp, p, i, d, sorb_or_he3pot):
        self.ca.assert_setting_setpoint_sets_readback("NO", "ADJUST_PIDS")
        self.ca.set_pv_value("P:SP", 0)
        self.ca.set_pv_value("I:SP", 0)
        self.ca.set_pv_value("D:SP", 0)
        self.ca.assert_setting_setpoint_sets_readback(f"{sorb_or_he3pot}_file.txt", f"{sorb_or_he3pot}:PID_FILE")
        self.ca.set_pv_value(f"TEMP:{sorb_or_he3pot}:SP", temp)
        self.ca.assert_that_pv_is_not("P", p)
        self.ca.assert_that_pv_is_not("I", i)
        self.ca.assert_that_pv_is_not("D", d)
        self.ca.assert_that_pv_is("P", 0)
        self.ca.assert_that_pv_is("I", 0)
        self.ca.assert_that_pv_is("D", 0)

    def test_WHEN_recondense_started_THEN_condensing_is_started_WHEN_steps_skipped_THEN_skipped_AND_temp_sp_set(self):
        # Set temp values
        self.ca.set_pv_value("TEMP:HE3POT:SP", 0.1)
        post_recondense_temp_sp = 0.3
        self.ca.assert_setting_setpoint_sets_readback(post_recondense_temp_sp, "RE:TEMP")
        self.set_unattainable_recondense_conditions()
        # Start recondensing and skip steps
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.ca.assert_that_pv_is("RE:PART", "PART 1")
        self.ca.set_pv_value("RE:SKIPPED:SP", "YES")
        self.ca.assert_that_pv_is("RE:PART", "PART 2")
        self.ca.set_pv_value("RE:SKIPPED:SP", "YES")
        self.ca.assert_that_pv_is("RE:PART", "PART 3")
        self.ca.set_pv_value("RE:SKIPPED:SP", "YES")
        # Assert that temperature setpoint is set
        self.ca.assert_that_pv_is_number("TEMP:HE3POT:SP", post_recondense_temp_sp, tolerance=0.001)

    @parameterized.expand(parameterized_list([0, 1, 2]))
    def test_WHEN_cancelled_in_any_step_THEN_temp_not_set_AND_cancelled(self, _, parts_skipped):
        # Set temp values
        original_temp_sp = 0.1
        self.ca.set_pv_value("TEMP:HE3POT:SP", original_temp_sp)
        post_recondense_temp_sp = 0.3
        self.ca.assert_setting_setpoint_sets_readback(post_recondense_temp_sp, "RE:TEMP")
        self.set_unattainable_recondense_conditions()
        # Start recondensing and skip steps
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.skip_parts(parts_skipped)
        self.ca.assert_setting_setpoint_sets_readback("YES", "RE:CANCELLED")
        self.ca.assert_that_pv_is("RE:PART", "NOT RECONDENSING")
        # Assert that temperature setpoint is set
        self.ca.assert_that_pv_is_number("TEMP:HE3POT:SP", original_temp_sp, tolerance=0.001)

    def test_WHEN_in_part_1_THEN_values_set_correctly(self):
        self.set_unattainable_recondense_conditions()
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.ca.assert_that_pv_is("RE:PART", "PART 1")
        self.ca.assert_that_pv_is("RE:SKIPPED", "NO")
        self.ca.assert_that_pv_is("RE:CANCELLED", "NO")
        self.ca.assert_that_pv_is("RE:TIMED_OUT", "NO")
        self.ca.assert_that_pv_is("ADJUST_PIDS", "NO")
        self.ca.assert_that_pv_is("MODE:HTR", "Manual")
        self.ca.assert_that_pv_is("CTRLCHANNEL", "SORB")
        self.ca.assert_that_pv_is_number("HEATERP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number(
            "TEMP:SORB:SP", UNATTAINABLE_RECONDENSE_VALUES["RE:SORB:TEMP:SP"], tolerance=0.001
        )
        self.ca.assert_that_pv_is_number("TEMP:SP", UNATTAINABLE_RECONDENSE_VALUES["RE:SORB:TEMP:SP"], tolerance=0.001)
        self.ca.assert_that_pv_is_number("P", IOCS[0]["macros"]["RECONDENSE_SORB_P"], tolerance=0.001)
        self.ca.assert_that_pv_is_number("I", IOCS[0]["macros"]["RECONDENSE_SORB_I"], tolerance=0.001)
        self.ca.assert_that_pv_is_number("D", IOCS[0]["macros"]["RECONDENSE_SORB_D"], tolerance=0.001)

    def test_WHEN_in_part_3_THEN_values_set_correctly(self):
        self.set_unattainable_recondense_conditions()
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.skip_parts(2)
        self.ca.assert_that_pv_is("RE:PART", "PART 3")
        self.ca.assert_that_pv_is("RE:SKIPPED", "NO")
        self.ca.assert_that_pv_is("RE:CANCELLED", "NO")
        self.ca.assert_that_pv_is("RE:TIMED_OUT", "NO")
        self.ca.assert_that_pv_is("ADJUST_PIDS", "NO")
        self.ca.assert_that_pv_is("MODE:HTR", "Manual")
        self.ca.assert_that_pv_is_number("HEATERP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("TEMP:SORB:SP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("TEMP:SP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("P", IOCS[0]["macros"]["RECONDENSE_SORB_P"], tolerance=0.001)
        self.ca.assert_that_pv_is_number("I", IOCS[0]["macros"]["RECONDENSE_SORB_I"], tolerance=0.001)
        self.ca.assert_that_pv_is_number("D", IOCS[0]["macros"]["RECONDENSE_SORB_D"], tolerance=0.001)
        self.ca.assert_that_pv_is("CTRLCHANNEL", "SORB")

    @parameterized.expand(parameterized_list([0.5, 1.2]))
    def test_WHEN_set_post_recondense_temp_AND_setpoint_is_less_than_max_he3_cooling_temp_THEN_post_recondense_set(
            self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "RE:TEMP")

    @parameterized.expand(parameterized_list([2.8, 12.2]))
    def test_WHEN_set_post_recondense_temp_AND_setpoint_is_greater_than_max_he3_cooling_temp_THEN_post_recondense_not_set(
            self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(
            temp, "RE:TEMP", expected_value=0.3, expected_alarm=self.ca.Alarms.MINOR
        )
        self.ca.assert_that_pv_alarm_is("RE:TEMP:SP", self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list([20.8, 100.2]))
    def test_WHEN_set_post_recondense_temp_AND_setpoint_is_greater_than_max_heliox_op_temp_THEN_post_recondense_not_set(
            self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "RE:TEMP", expected_value=0.3, expected_alarm=self.ca.Alarms.MAJOR)
        self.ca.assert_that_pv_alarm_is("RE:TEMP:SP", self.ca.Alarms.MAJOR)

    @parameterized.expand(parameterized_list([12.0, 15.0]))
    def test_WHEN_set_final_recondense_sorb_temp_THEN_final_recondense_sorb_temp_set(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "RE:SORB:TEMP:FIN")

    @parameterized.expand(parameterized_list([12.0, 15.0]))
    def test_WHEN_set_recondense_sorb_temp_set_THEN_recondense_sorb_temp_set_set(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "RE:SORB:TEMP")

    @parameterized.expand(parameterized_list(product(["P", "I", "D"], PID_TEST_VALUES)))
    def test_WHEN_set_recondense_sorb_pids_THEN_recondense_sorb_pids_set(self, _, p_or_i_or_d, val):
        self.ca.assert_setting_setpoint_sets_readback(val, f"RE:SORB:{p_or_i_or_d}")

    @parameterized.expand(parameterized_list([3, 10]))
    def test_WHEN_set_post_part_2_recondense_wait_time_THEN_post_part_2_recondense_wait_time_set(self, _, time):
        self.ca.assert_setting_setpoint_sets_readback(time, "RE:PART2:WAIT_TIME")

    @parameterized.expand(parameterized_list(product([1, 2], [1.8, 2.2])))
    def test_WHEN_set_he3pot_targets_THEN_he3pot_targets_set(self, _, part, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, f"RE:HE3POT:TEMP:PART{part}")

    @parameterized.expand(parameterized_list([1.4, 3.2]))
    def test_WHEN_set_max_temp_he3_cooling_THEN_max_temp_he3_cooling_set(self, _, max_temp_for_he3_cooling):
        self.ca.assert_setting_setpoint_sets_readback(max_temp_for_he3_cooling, "MAX_TEMP_FOR_HE3_COOLING")

    @parameterized.expand(parameterized_list([
        (1.4, 0.8, "1KPOTHE3POTLO", "1KPOTHE3POTLO"), (1.4, 1.9, "1KPOTHE3POTLO", "HE3POTHI"),
        (3.2, 2.1, "HE3POTHI", "1KPOTHE3POTLO"), (3.2, 3.8, "HE3POTHI", "HE3POTHI")]))
    def test_WHEN_set_max_temp_he3_cooling_THEN_correct_control_channel_used(
            self, _, max_temp_for_he3_cooling, temp, previous_expected_ctrl_channel, new_expected_ctrl_channel):
        self.ca.set_pv_value("TEMP:HE3POT:SP", temp)
        self.ca.assert_that_pv_is("CTRLCHANNEL", previous_expected_ctrl_channel)
        self.ca.assert_setting_setpoint_sets_readback(max_temp_for_he3_cooling, "MAX_TEMP_FOR_HE3_COOLING")
        self.ca.set_pv_value("TEMP:HE3POT:SP", temp)
        self.ca.assert_that_pv_is("CTRLCHANNEL", new_expected_ctrl_channel)

    def assert_recondense_temp_alarm_is(self, minor: bool):
        if minor:
            self.ca.assert_that_pv_alarm_is("RE:TEMP:SP", self.ca.Alarms.MINOR)
            self.ca.assert_that_pv_alarm_is("RE:TEMP", self.ca.Alarms.MINOR)
        else:
            self.ca.assert_that_pv_alarm_is("RE:TEMP:SP", self.ca.Alarms.NONE)
            self.ca.assert_that_pv_alarm_is("RE:TEMP", self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list([(1.4, False), (3.2, True)]))
    def test_WHEN_set_max_temp_he3_cooling_THEN_high_value_set_on_recondense_temp_sp_AND_alarms_correct(
            self, _, max_temp_for_he3_cooling, alarm_expected):
        self.ca.set_pv_value("RE:TEMP:SP", max_temp_for_he3_cooling + 0.1)
        self.assert_recondense_temp_alarm_is(alarm_expected)
        self.ca.assert_setting_setpoint_sets_readback(max_temp_for_he3_cooling, "MAX_TEMP_FOR_HE3_COOLING")
        self.ca.assert_that_pv_is("RE:TEMP:SP.HIGH", max_temp_for_he3_cooling)
        self.ca.assert_that_pv_alarm_is("RE:TEMP:SP", self.ca.Alarms.MINOR)
        self.ca.assert_that_pv_alarm_is("RE:TEMP", self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list([(1.4, False), (3.2, True)]))
    def test_WHEN_set_max_temp_he3_cooling_THEN_low_value_set_on_recondense_temp_sp_AND_alarms_correct(
            self, _, max_temp_for_he3_cooling, alarm_expected):
        self.ca.set_pv_value("RE:TEMP:SP", max_temp_for_he3_cooling - 0.1)
        self.assert_recondense_temp_alarm_is(alarm_expected)
        self.ca.assert_setting_setpoint_sets_readback(max_temp_for_he3_cooling, "MAX_TEMP_FOR_HE3_COOLING")
        self.ca.assert_that_pv_is("RE:TEMP:SP.HIGH", max_temp_for_he3_cooling)
        self.ca.assert_that_pv_alarm_is("RE:TEMP:SP", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_alarm_is("RE:TEMP", self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(["YES", "NO"]))
    def test_WHEN_set_timeout_on_or_off_THEN_timeout_on_or_off_set(self, _, on_or_off):
        self.ca.assert_setting_setpoint_sets_readback(on_or_off, "RE:TIMEOUT:ON")

    @parameterized.expand(parameterized_list([2, 30]))
    def test_WHEN_set_timeout_THEN_timeout_set(self, _, timeout):
        self.ca.assert_setting_setpoint_sets_readback(timeout, "RE:TIMEOUT")

    def skip_parts(self, number_of_parts_to_skip: int, part_offset: int = 0, assert_parts=True):
        for i in range(number_of_parts_to_skip):
            if assert_parts:
                self.ca.assert_that_pv_is("RE:PART", f"PART {i+1+part_offset}")
            self.ca.set_pv_value("RE:SKIPPED:SP", "YES")

    @parameterized.expand(parameterized_list([0, 1, 2]))
    def test_WHEN_timed_out_in_any_step_THEN_temp_set_AND_timed_out(self, _, parts_skipped):
        # Set temp values
        original_temp_sp = 0.1
        self.ca.set_pv_value("TEMP:HE3POT:SP", original_temp_sp)
        post_recondense_temp_sp = 0.3
        self.ca.assert_setting_setpoint_sets_readback(post_recondense_temp_sp, "RE:TEMP")
        self.set_unattainable_recondense_conditions()
        # Start recondensing and skip steps
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.skip_parts(parts_skipped)
        self.ca.assert_setting_setpoint_sets_readback(1, "RE:TIMEOUT")
        self.ca.assert_that_pv_is("RE:TIMED_OUT", "YES", timeout=3)
        self.ca.assert_that_pv_is("RE:PART", "NOT RECONDENSING")
        # Assert that temperature setpoint is set
        self.ca.assert_that_pv_is_number("TEMP:HE3POT:SP", post_recondense_temp_sp, tolerance=0.001)

    @parameterized.expand(parameterized_list([0, 1, 2]))
    def test_WHEN_time_out_off_in_any_step_AND_wait_AND_cancel_THEN_temp_not_set_AND_timed_out(self, _, parts_skipped):
        # Set temp values
        original_temp_sp = 0.1
        self.ca.set_pv_value("TEMP:HE3POT:SP", original_temp_sp)
        post_recondense_temp_sp = 0.3
        self.ca.assert_setting_setpoint_sets_readback(post_recondense_temp_sp, "RE:TEMP")
        self.set_unattainable_recondense_conditions()
        # Start recondensing and skip steps
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.skip_parts(parts_skipped)
        self.ca.assert_setting_setpoint_sets_readback("NO", "RE:TIMEOUT:ON")
        self.ca.set_pv_value("RE:TIMEOUT:SP", 1, sleep_after_set=2)
        self.ca.assert_that_pv_is("RE:TIMED_OUT", "NO", timeout=3)
        self.ca.set_pv_value("RE:CANCELLED:SP", "YES")
        self.ca.assert_that_pv_is("RE:PART", "NOT RECONDENSING")
        # Assert that temperature setpoint is set
        self.ca.assert_that_pv_is_number("TEMP:HE3POT:SP", original_temp_sp, tolerance=0.001)

    @parameterized.expand(parameterized_list([
        # Set targets that aren't reasonable to test different paths
        {}, {"RE:SORB:TEMP:SP": UNATTAINABLE_RECONDENSE_VALUES["RE:SORB:TEMP:SP"]},
        {"RE:HE3POT:TEMP:PART1:SP": UNATTAINABLE_RECONDENSE_VALUES["RE:HE3POT:TEMP:PART1:SP"]},
        {"RE:HE3POT:TEMP:PART2:SP": UNATTAINABLE_RECONDENSE_VALUES["RE:HE3POT:TEMP:PART2:SP"]}
    ]))
    @skip_if_recsim("Backdoor not available in recsim")
    def test_WHEN_recondense_THEN_recondense(self, _, pv_sets):
        # Set requirement for recondense
        self._lewis.backdoor_set_on_device("helium_3_pot_empty", True)
        # Set temp values
        original_temp_sp = 0.1
        self.ca.set_pv_value("TEMP:HE3POT:SP", original_temp_sp)
        post_recondense_temp_sp = 0.3
        self.ca.assert_setting_setpoint_sets_readback(post_recondense_temp_sp, "RE:TEMP")
        # Set state for recondense
        self.ca.set_pv_value("RE:PART2:WAIT_TIME", 1)
        for pv, set_point in pv_sets.items():
            self.ca.set_pv_value(pv, set_point)
        # Initiate recondense
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        # Wait for recondense to finish
        self.ca.assert_that_pv_is("RE:PART", "PART 1", timeout=10)
        self.ca.assert_that_pv_is("RE:PART", "PART 2", timeout=10)
        self.ca.assert_that_pv_is("RE:PART", "PART 3", timeout=10)
        self.ca.assert_that_pv_is("RECONDENSING", "NO", timeout=10)
        self.ca.assert_that_pv_is("RE:SUCCESS", "YES")
        self._lewis.backdoor_set_on_device("helium_3_pot_empty", False)
        self.ca.assert_that_pv_is_number("TEMP:HE3POT:SP", post_recondense_temp_sp, tolerance=0.001)
        self.ca.assert_that_pv_is_number("TEMP:HE3POT", post_recondense_temp_sp, tolerance=0.001)
        # Assert post condense status
        self.ca.assert_that_pv_is("RE:CANCELLED", "NO")
        self.ca.assert_that_pv_is("RE:TIMED_OUT", "NO")
        self.ca.assert_that_pv_is("RE:SKIPPED", "NO")
        self.ca.assert_that_pv_is("RE:PART", "NOT RECONDENSING")

    def assert_pid_values(self, pid_value: float, pv_prefix: str = "", pv_suffix: str = "", timeouts: int = None):
        for pid in ["P", "I", "D"]:
            self.ca.assert_that_pv_is_number(
                f"{pv_prefix}{pid}{pv_suffix}", pid_value, timeout=timeouts, tolerance=0.0001
            )

    def assert_pid_settings(self, adjust_pids: str, autopid: str, pid_value: float,
                            pv_prefix: str = "", pv_suffix: str = "", timeouts: int = None):
        self.ca.assert_that_pv_is(f"{pv_prefix}ADJUST_PIDS{pv_suffix}", adjust_pids, timeout=timeouts)
        self.ca.assert_that_pv_is(f"{pv_prefix}AUTOPID{pv_suffix}", autopid, timeout=timeouts)
        self.assert_pid_values(pid_value, pv_prefix, pv_suffix, timeouts)

    def set_pid_values(self, pid_value: float, pv_prefix: str = ""):
        for pid in ["P", "I", "D"]:
            self.ca.set_pv_value(f"{pv_prefix}{pid}:SP", pid_value)

    def set_pid_settings(self, adjust_pids: str, autopid: str, pid_value: float):
        self.ca.set_pv_value("AUTOPID:SP", autopid)
        self.ca.set_pv_value("ADJUST_PIDS:SP", adjust_pids)
        self.set_pid_values(pid_value)


    def test_WHEN_recondense_THEN_after_recondense_pid_settings_are_restored(self):
        self.set_unattainable_recondense_conditions()
        # Set up old values
        old_autopid_value = "ON"
        old_adjust_pid_value = "YES"
        old_pid_values = 0.0
        self.set_pid_settings(old_adjust_pid_value, old_autopid_value, old_pid_values)
        # Set up expected in-recondense values
        new_pid_values = 1.8
        self.set_pid_values(new_pid_values, pv_prefix="RE:SORB:")
        new_autopid_value = "OFF"
        new_adjust_pid_value = "NO"
        # Commence recondense
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        # Assert Old PID settings stored and new PID settings set
        self.assert_pid_settings(
            old_adjust_pid_value, old_autopid_value, old_pid_values, pv_prefix="RE:_OLD_", timeouts=2
        )
        self.assert_pid_settings(new_adjust_pid_value, new_autopid_value, new_pid_values)
        self.skip_parts(3, assert_parts=False)
        # Assert recondense finished
        self.ca.assert_setting_setpoint_sets_readback("NO", "RECONDENSING", timeout=10)
        # Assert old PID settings reapplied
        self.assert_pid_settings(old_adjust_pid_value, old_autopid_value, old_pid_values)
