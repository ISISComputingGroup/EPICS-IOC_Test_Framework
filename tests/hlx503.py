import unittest

from parameterized import parameterized

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim
from genie_python.utilities import dehex_and_decompress

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
            "MAX_OPERATING_TEMP_FOR_HELIOX": 20.0
        }
    },
]

channels = {
    "SORB": "SORB",
    "HE3POT": "HE3POTHI"
}


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

PID_TABLE_LOOKUP_VALUES = [
    (0.6, 10.0, 11.0, 12.0, "SORB"), (4.0, 20.0, 21.0, 22.0, "SORB"), (5.8, 30.0, 31.0, 32.0, "SORB"),
    (0.6, 13.0, 14.0, 15.0, "HE3POT"), (4.0, 23.0, 24.0, 25.0, "HE3POT"), (5.8, 33.0, 34.0, 35.0, "HE3POT")
]


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

        self.ca.set_pv_value("RECONDENSE:CANCELLED:SP", "YES")
        self.ca.assert_that_pv_is("RECONDENSING", "NO")

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

    @parameterized.expand(parameterized_list(["SORB", "HE3POTHI", "1KPOTHE3POTLO"]))
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_ctrlchannel_set_THEN_ctrlchannel_set(self, _, new_control_channel):
        self.ca.assert_setting_setpoint_sets_readback(new_control_channel, "CTRLCHANNEL")

    @parameterized.expand(parameterized_list([0.2, 3.8]))
    def test_WHEN_proportional_set_THEN_proportional_set(self, _, proportional):
        self.ca.assert_setting_setpoint_sets_readback(proportional, "P")

    @parameterized.expand(parameterized_list([0.2, 3.8]))
    def test_WHEN_integral_set_THEN_integral_set(self, _, integral):
        self.ca.assert_setting_setpoint_sets_readback(integral, "I")

    @parameterized.expand(parameterized_list([0.2, 3.8]))
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
        self.ca.assert_setting_setpoint_sets_readback(
            post_recondense_temp_sp, "RECONDENSE:TEMP:SP:RBV", set_point_pv="RECONDENSE:TEMP:SP"
        )
        # Start recondensing and skip steps
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.ca.assert_that_pv_is("RECONDENSE:PART", "PART 1")
        self.ca.set_pv_value("RECONDENSE:SKIPPED:SP", "YES")
        self.ca.assert_that_pv_is("RECONDENSE:PART", "PART 2")
        self.ca.set_pv_value("RECONDENSE:SKIPPED:SP", "YES")
        self.ca.assert_that_pv_is("RECONDENSE:PART", "PART 3")
        self.ca.set_pv_value("RECONDENSE:SKIPPED:SP", "YES")
        # Assert that temperature setpoint is set
        self.ca.assert_that_pv_is_number("TEMP:HE3POT:SP", post_recondense_temp_sp, tolerance=0.001)

    @parameterized.expand(parameterized_list([0, 1, 2]))
    def test_WHEN_cancelled_in_any_step_THEN_temp_not_set_AND_cancelled(self, _, parts_skipped):
        # Set temp values
        original_temp_sp = 0.1
        self.ca.set_pv_value("TEMP:HE3POT:SP", original_temp_sp)
        post_recondense_temp_sp = 0.3
        self.ca.assert_setting_setpoint_sets_readback(
            post_recondense_temp_sp, "RECONDENSE:TEMP:SP:RBV", set_point_pv="RECONDENSE:TEMP:SP"
        )
        # Start recondensing and skip steps
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        for i in range(parts_skipped):
            self.ca.assert_that_pv_is("RECONDENSE:PART", f"PART {i+1}")
            self.ca.set_pv_value("RECONDENSE:SKIPPED:SP", "YES")
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSE:CANCELLED")
        self.ca.assert_that_pv_is("RECONDENSE:PART", "NOT RECONDENSING")
        # Assert that temperature setpoint is set
        self.ca.assert_that_pv_is_number("TEMP:HE3POT:SP", original_temp_sp, tolerance=0.001)

    def test_WHEN_in_part_1_THEN_values_set_correctly(self):
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.ca.assert_that_pv_is("RECONDENSE:PART", "PART 1")
        self.ca.assert_that_pv_is("RECONDENSE:SKIPPED", "NO")
        self.ca.assert_that_pv_is("RECONDENSE:CANCELLED", "NO")
        self.ca.assert_that_pv_is("RECONDENSE:TIMED_OUT", "NO")
        self.ca.assert_that_pv_is("ADJUST_PIDS", "NO")
        self.ca.assert_that_pv_is("MODE:HTR", "Manual")
        self.ca.assert_that_pv_is_number("HEATERP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("TEMP:SORB:SP", 33.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("TEMP:SP", 33.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("P", 1.2, tolerance=0.001)
        self.ca.assert_that_pv_is_number("I", 1.2, tolerance=0.001)
        self.ca.assert_that_pv_is_number("D", 1.2, tolerance=0.001)
        self.ca.assert_that_pv_is("CTRLCHANNEL", "1KPOTHE3POTLO")

    def test_WHEN_in_part_3_THEN_values_set_correctly(self):
        self.ca.assert_setting_setpoint_sets_readback("YES", "RECONDENSING")
        self.ca.set_pv_value("RECONDENSE:SKIPPED:SP", "YES")
        self.ca.set_pv_value("RECONDENSE:SKIPPED:SP", "YES")
        self.ca.assert_that_pv_is("RECONDENSE:PART", "PART 3")
        self.ca.assert_that_pv_is("RECONDENSE:SKIPPED", "NO")
        self.ca.assert_that_pv_is("RECONDENSE:CANCELLED", "NO")
        self.ca.assert_that_pv_is("RECONDENSE:TIMED_OUT", "NO")
        self.ca.assert_that_pv_is("ADJUST_PIDS", "NO")
        self.ca.assert_that_pv_is("MODE:HTR", "Manual")
        self.ca.assert_that_pv_is_number("HEATERP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("TEMP:SORB:SP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("TEMP:SP", 0.0, tolerance=0.001)
        self.ca.assert_that_pv_is_number("P", 1.2, tolerance=0.001)
        self.ca.assert_that_pv_is_number("I", 1.2, tolerance=0.001)
        self.ca.assert_that_pv_is_number("D", 1.2, tolerance=0.001)
        self.ca.assert_that_pv_is("CTRLCHANNEL", "SORB")

    @parameterized.expand(parameterized_list(["SETUP", "PART 1", "PART 2", "PART 3", "FINISHING", "NOT RECONDENSING"]))
    def test_WHEN_set_part_THEN_part_set(self, _, part):
        self.ca.assert_setting_setpoint_sets_readback(part, "RECONDENSE:PART")

    @parameterized.expand(parameterized_list(["YES", "NO"]))
    def test_WHEN_set_timed_out_THEN_timed_out_set(self, _, timed_out):
        self.ca.assert_setting_setpoint_sets_readback(timed_out, "RECONDENSE:TIMED_OUT")

    @parameterized.expand(parameterized_list(["YES", "NO"]))
    def test_WHEN_set_skipped_THEN_skipped_set(self, _, skipped):
        self.ca.assert_setting_setpoint_sets_readback(skipped, "RECONDENSE:SKIPPED")

    @parameterized.expand(parameterized_list([0.5, 1.2]))
    def test_WHEN_set_post_recondense_temp_AND_setpoint_is_less_than_max_he3_cooling_temp_THEN_post_recondense_set(
            self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "RECONDENSE:TEMP:SP:RBV", set_point_pv="RECONDENSE:TEMP:SP")

    @parameterized.expand(parameterized_list([2.8, 12.2]))
    def test_WHEN_set_post_recondense_temp_AND_setpoint_is_greater_than_max_he3_cooling_temp_THEN_post_recondense_not_set(
            self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(
            temp, "RECONDENSE:TEMP:SP:RBV", set_point_pv="RECONDENSE:TEMP:SP", expected_value=0.3
        )
        self.ca.assert_that_pv_alarm_is("RECONDENSE:TEMP:SP", self.ca.Alarms.MINOR)

    @parameterized.expand(parameterized_list([20.8, 100.2]))
    def test_WHEN_set_post_recondense_temp_AND_setpoint_is_greater_than_max_heliox_op_temp_THEN_post_recondense_not_set(
            self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(
            temp, "RECONDENSE:TEMP:SP:RBV", set_point_pv="RECONDENSE:TEMP:SP", expected_value=0.3
        )
        self.ca.assert_that_pv_alarm_is("RECONDENSE:TEMP:SP", self.ca.Alarms.MAJOR)

    @parameterized.expand(parameterized_list([0.5, 1.2]))
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_forward_post_condense_temp_setpoint_THEN_temp_set(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "RECONDENSE:TEMP:SP:RBV", set_point_pv="RECONDENSE:TEMP:SP")
        self.ca.process_pv("RECONDENSE:TEMP:_FORWARD")
        self.ca.assert_that_pv_is("CTRLCHANNEL", "1KPOTHE3POTLO")
        self.ca.assert_that_pv_is("TEMP:HE3POT:SP", temp)
        self.ca.assert_that_pv_is("TEMP:HE3POT", temp)
