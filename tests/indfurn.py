import unittest
from time import sleep

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

DEVICE_PREFIX = "INDFURN_01"
EMULATOR_NAME = "indfurn"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("INDFURN"),
        "emulator": EMULATOR_NAME,
        "macros": {
            "ARBITRARY_ASG": "DEFAULT",  # defaults to manager mode only but we want can't change manager mode in tests
        }
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

TEST_TEMPERATURES = [0.01, 123.45, 9999.99]  # 2 d.p. precision, up to 9999.99
TEST_DIAGNOSTIC_TEMPERATURES = [0.1, 123.7, 999.9]  # 1 d.p. presision, up to 999.9
TEST_PID_VALUES = TEST_DIAGNOSTIC_TEMPERATURES
TEST_OUTPUTS = TEST_DIAGNOSTIC_TEMPERATURES
TEST_SAMPLE_TIMES = [0, 1, 999999]
TEST_PID_LIMITS = TEST_TEMPERATURES
TEST_PSU_VOLTAGES = [0.01, 123.45, 999.99]
TEST_PSU_CURRENTS = TEST_PSU_VOLTAGES


class IndfurnTests(unittest.TestCase):
    """
    Tests for the Indfurn IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_that_disable_pv_exists(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_that_version_pv_exists(self):
        self.ca.assert_that_pv_is("VERSION",
                                  "INDFURN RECSIM" if IOCRegister.uses_rec_sim else "EMULATED INDUCTION FURNACE")

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_GIVEN_a_setpoint_WHEN_ask_for_the_setpoint_readback_THEN_get_the_value_just_set(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, set_point_pv="TEMP:SP", readback_pv="TEMP:SP:RBV")

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_GIVEN_a_setpoint_WHEN_ask_for_the_current_temperature_THEN_get_the_value_just_set(self, _, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, set_point_pv="TEMP:SP", readback_pv="TEMP")

    @parameterized.expand(parameterized_list(TEST_DIAGNOSTIC_TEMPERATURES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_pipe_temperature_set_via_backdoor_when_read_pipe_temperature_THEN_get_value_just_set(self, _, temp):
        self._lewis.backdoor_set_on_device("pipe_temperature", temp)
        self.ca.assert_that_pv_is_number("PIPE:TEMP", temp, tolerance=0.1)

    @parameterized.expand(parameterized_list(TEST_DIAGNOSTIC_TEMPERATURES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_capacitor_temperature_set_via_backdoor_when_read_capacitor_temperature_THEN_get_value_just_set(self, _, temp):
        self._lewis.backdoor_set_on_device("capacitor_bank_temperature", temp)
        self.ca.assert_that_pv_is_number("CAPACITOR:TEMP", temp, tolerance=0.1)

    @parameterized.expand(parameterized_list(TEST_DIAGNOSTIC_TEMPERATURES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_fet_temperature_set_via_backdoor_when_read_fet_temperature_THEN_get_value_just_set(self, _, temp):
        self._lewis.backdoor_set_on_device("fet_temperature", temp)
        self.ca.assert_that_pv_is_number("FET:TEMP", temp, tolerance=0.1)

    @parameterized.expand(parameterized_list(TEST_PID_VALUES))
    def test_GIVEN_p_parameter_changed_WHEN_read_p_THEN_value_can_be_read_back(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(val, "P")

    @parameterized.expand(parameterized_list(TEST_PID_VALUES))
    def test_GIVEN_i_parameter_changed_WHEN_read_i_THEN_value_can_be_read_back(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(val, "I")

    @parameterized.expand(parameterized_list(TEST_PID_VALUES))
    def test_GIVEN_d_parameter_changed_WHEN_read_d_THEN_value_can_be_read_back(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(val, "D")

    @parameterized.expand(parameterized_list(TEST_SAMPLE_TIMES))
    def test_GIVEN_sample_time_changed_WHEN_read_sample_time_THEN_value_can_be_read_back(self, _, sample_time):
        self.ca.assert_setting_setpoint_sets_readback(sample_time, "SAMPLETIME")

    def test_GIVEN_pid_direction_is_set_THEN_it_can_be_read_back(self):
        for mode in ["Heating", "Cooling", "Heating"]:  # Check both transitions
            self.ca.assert_setting_setpoint_sets_readback(mode, "PID:DIRECTION")

    @parameterized.expand(parameterized_list(TEST_PID_LIMITS))
    def test_GIVEN_pid_lower_limit_is_set_THEN_it_can_be_read_back(self, _, pid_limit):
        self.ca.assert_setting_setpoint_sets_readback(pid_limit, "PID:LIMIT:LOWER")

    @parameterized.expand(parameterized_list(TEST_PID_LIMITS))
    def test_GIVEN_pid_upper_limit_is_set_THEN_it_can_be_read_back(self, _, pid_limit):
        self.ca.assert_setting_setpoint_sets_readback(pid_limit, "PID:LIMIT:UPPER")

    @parameterized.expand(parameterized_list(TEST_PSU_VOLTAGES))
    def test_GIVEN_psu_voltage_is_set_THEN_it_can_be_read_back(self, _, psu_volt):
        self.ca.assert_setting_setpoint_sets_readback(psu_volt, "PSU:VOLT")

    @parameterized.expand(parameterized_list(TEST_PSU_CURRENTS))
    def test_GIVEN_psu_current_is_set_THEN_it_can_be_read_back(self, _, psu_curr):
        self.ca.assert_setting_setpoint_sets_readback(psu_curr, "PSU:CURR")

    @parameterized.expand(parameterized_list(TEST_OUTPUTS))
    def test_GIVEN_output_is_set_THEN_it_can_be_read_back(self, _, output):
        self.ca.assert_setting_setpoint_sets_readback(output, "OUTPUT")

    def test_GIVEN_pid_mode_is_set_THEN_it_can_be_read_back(self):
        for mode in ["Automatic", "Manual", "Automatic"]:  # Check both transitions
            self.ca.assert_setting_setpoint_sets_readback(mode, "PID:MODE")

    def _wait_for_lewis_backdoor(self, variable_name, expected, max_attempts=10, sleep_interval=0.1):
        for _ in range(max_attempts):
            try:
                self.assertEqual(self._lewis.backdoor_get_from_device(variable_name), str(expected))
                break
            except AssertionError as e:
                err = e
                sleep(sleep_interval)
        else:
            raise err

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_power_supply_mode_is_set_to_either_local_or_remote_THEN_it_sets_successfully_in_emulator(self):
        for remote in [False, True, False]:  # Check both transitions
            self.ca.set_pv_value("PSU:CONTROLMODE:SP", "Remote" if remote else "Local")
            self._wait_for_lewis_backdoor("remote_mode", remote)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_power_supply_output_is_set_to_either_on_or_off_THEN_it_sets_successfully_in_emulator(self):
        for output in [False, True, False]:  # Check both transitions
            self.ca.set_pv_value("PSU:POWER:SP", "On" if output else "Off")
            self._wait_for_lewis_backdoor("power_supply_on", output)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_power_supply_fan_is_set_to_either_on_or_off_THEN_it_sets_successfully_in_emulator(self):
        for fan_on in [False, True, False]:  # Check both transitions
            self.ca.set_pv_value("PSU:FAN:SP", "On" if fan_on else "Off")
            self._wait_for_lewis_backdoor("power_supply_fan_on", fan_on)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_power_supply_hf_is_set_to_either_on_or_off_THEN_it_sets_successfully_in_emulator(self):
        for hf_on in [False, True, False]:  # Check both transitions
            self.ca.set_pv_value("PSU:HF:SP", "On" if hf_on else "Off")
            self._wait_for_lewis_backdoor("hf_on", hf_on)

    @skip_if_recsim("Can't use lewis backdoor in recsim")
    def test_GIVEN_psu_goes_over_temperature_THEN_alarm_comes_on_AND_can_reset_via_pv(self):
        self._lewis.backdoor_set_on_device("psu_overtemp", True)
        self.ca.assert_that_pv_is("ALARM:PSUTEMP", "ALARM")
        self.ca.assert_that_pv_alarm_is("ALARM:PSUTEMP", self.ca.Alarms.MAJOR)
        self.ca.set_pv_value("ALARM:CLEAR", 1)
        self.ca.assert_that_pv_is("ALARM:PSUTEMP", "OK")
        self.ca.assert_that_pv_alarm_is("ALARM:PSUTEMP", self.ca.Alarms.NONE)

    @skip_if_recsim("Can't use lewis backdoor in recsim")
    def test_GIVEN_psu_goes_over_voltage_THEN_alarm_comes_on_AND_can_reset_via_pv(self):
        self._lewis.backdoor_set_on_device("psu_overvolt", True)
        self.ca.assert_that_pv_is("ALARM:PSUVOLT", "ALARM")
        self.ca.assert_that_pv_alarm_is("ALARM:PSUVOLT", self.ca.Alarms.MAJOR)
        self.ca.set_pv_value("ALARM:CLEAR", 1)
        self.ca.assert_that_pv_is("ALARM:PSUVOLT", "OK")
        self.ca.assert_that_pv_alarm_is("ALARM:PSUVOLT", self.ca.Alarms.NONE)

    @skip_if_recsim("Can't use lewis backdoor in recsim")
    def test_GIVEN_cooling_water_flow_turns_off_THEN_this_is_visible_from_ioc_and_causes_alarm(self):
        self._lewis.backdoor_set_on_device("cooling_water_flow", False)
        self.ca.assert_that_pv_is("COOLINGWATERFLOW", "ALARM")
        self.ca.assert_that_pv_alarm_is("COOLINGWATERFLOW", self.ca.Alarms.MAJOR)

        self._lewis.backdoor_set_on_device("cooling_water_flow", True)
        self.ca.assert_that_pv_is("COOLINGWATERFLOW", "OK")
        self.ca.assert_that_pv_alarm_is("COOLINGWATERFLOW", self.ca.Alarms.NONE)

    @skip_if_recsim("Recsim can't handle arbitrary commands")
    def test_GIVEN_an_arbitrary_command_THEN_get_a_response(self):
        self.ca.set_pv_value("ARBITRARY:SP", "?ver")
        self.ca.assert_that_pv_is("ARBITRARY", "<EMULATED INDUCTION FURNACE")
