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

TEST_TEMPERATURES = [
    (123.45, ChannelAccess.Alarms.NONE),
    (9999.99, ChannelAccess.Alarms.MAJOR),
]

TEST_DIAGNOSTIC_TEMPERATURES = [
    (23.4, ChannelAccess.Alarms.NONE),
    (999.9, ChannelAccess.Alarms.MAJOR),
]

TEST_PID_VALUES = [23.4, 999.9]
TEST_OUTPUTS = TEST_PID_VALUES
TEST_SAMPLE_TIMES = [0, 1, 999999]
TEST_PID_LIMITS = [0.0, 0.1, 99.9]
TEST_PSU_VOLTAGES = [0.01, 123.45, 999.99]
TEST_PSU_CURRENTS = TEST_PSU_VOLTAGES

SAMPLE_HOLDER_MATERIALS = [
    "Aluminium",
    "Glassy Carbon",
    "Graphite",
    "Quartz",
    "Single Crystal Sapphire",
    "Steel",
    "Vanadium",
]


class IndfurnTests(unittest.TestCase):
    """
    Tests for the Indfurn IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

    def test_that_disable_pv_exists(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skip_if_recsim("Recsim does not emulate version command")
    def test_that_version_pv_exists(self):
        self.ca.assert_that_pv_is("VERSION", "EMULATED FURNACE")

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_GIVEN_a_setpoint_WHEN_ask_for_the_setpoint_readback_THEN_get_the_value_just_set(self, _, temp, alarm):
        self.ca.assert_setting_setpoint_sets_readback(
            temp, set_point_pv="TEMP:SP", readback_pv="TEMP:SP:RBV", expected_alarm=alarm)

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_GIVEN_a_setpoint_WHEN_ask_for_the_current_temperature_THEN_get_the_value_just_set(self, _, temp, alarm):
        self.ca.assert_setting_setpoint_sets_readback(
            temp, set_point_pv="TEMP:SP", readback_pv="TEMP", expected_alarm=alarm)

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_GIVEN_a_setpoint_WHEN_ask_for_the_sample_temperature_THEN_get_the_value_just_set(self, _, temp, alarm):
        self.ca.assert_setting_setpoint_sets_readback(
            temp, set_point_pv="TEMP:SP", readback_pv="SAMPLE:TEMP", expected_alarm=alarm)

    @parameterized.expand(parameterized_list(TEST_DIAGNOSTIC_TEMPERATURES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_pipe_temperature_set_via_backdoor_when_read_pipe_temperature_THEN_get_value_just_set(self, _, temp, alarm):
        self._lewis.backdoor_set_on_device("pipe_temperature", temp)
        self.ca.assert_that_pv_is_number("PIPE:TEMP", temp, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("PIPE:TEMP", alarm)

    @parameterized.expand(parameterized_list(TEST_DIAGNOSTIC_TEMPERATURES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_capacitor_temperature_set_via_backdoor_when_read_capacitor_temperature_THEN_get_value_just_set(self, _, temp, alarm):
        self._lewis.backdoor_set_on_device("capacitor_bank_temperature", temp)
        self.ca.assert_that_pv_is_number("CAPACITOR:TEMP", temp, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("CAPACITOR:TEMP", alarm)

    @parameterized.expand(parameterized_list(TEST_DIAGNOSTIC_TEMPERATURES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_fet_temperature_set_via_backdoor_when_read_fet_temperature_THEN_get_value_just_set(self, _, temp, alarm):
        self._lewis.backdoor_set_on_device("fet_temperature", temp)
        self.ca.assert_that_pv_is_number("FET:TEMP", temp, tolerance=0.1)
        self.ca.assert_that_pv_alarm_is("FET:TEMP", alarm)

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

    def test_GIVEN_pid_run_status_is_set_THEN_it_can_be_read_back(self):
        for mode in ["Stopped", "Running", "Stopped"]:  # Check both transitions
            self.ca.assert_setting_setpoint_sets_readback(mode, "PID:RUNNING")

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

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_power_supply_mode_is_set_to_either_local_or_remote_THEN_it_sets_successfully_in_emulator(self):
        for remote in [False, True, False]:  # Check both transitions
            self.ca.assert_setting_setpoint_sets_readback("Remote" if remote else "Local", "PSU:CONTROLMODE",
                                                          expected_alarm=self.ca.Alarms.NONE if remote else self.ca.Alarms.MAJOR)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_power_supply_output_is_set_to_either_on_or_off_THEN_it_sets_successfully_in_emulator(self):
        for output in [False, True, False]:  # Check both transitions
            self.ca.assert_setting_setpoint_sets_readback("On" if output else "Off", "PSU:POWER")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sample_area_led_is_set_to_either_on_or_off_THEN_it_sets_successfully_in_emulator(self):
        for led_on in [False, True, False]:  # Check both transitions
            self.ca.assert_setting_setpoint_sets_readback("On" if led_on else "Off", "LED")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_power_supply_hf_is_set_to_either_on_or_off_THEN_it_sets_successfully_in_emulator(self):
        for hf_on in [False, True, False]:  # Check both transitions
            self.ca.assert_setting_setpoint_sets_readback("On" if hf_on else "Off", "PSU:HF")

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

        self._lewis.backdoor_set_on_device("cooling_water_flow", 0)
        self.ca.assert_that_pv_is("COOLINGWATER:FLOW", 0)
        self.ca.assert_that_pv_is("COOLINGWATER:STATUS", "ALARM")
        self.ca.assert_that_pv_alarm_is("COOLINGWATER:STATUS", self.ca.Alarms.MAJOR)

        self._lewis.backdoor_set_on_device("cooling_water_flow", 500)
        self.ca.assert_that_pv_is("COOLINGWATER:FLOW", 500)
        self.ca.assert_that_pv_is("COOLINGWATER:STATUS", "OK")
        self.ca.assert_that_pv_alarm_is("COOLINGWATER:STATUS", self.ca.Alarms.NONE)

    @skip_if_recsim("Recsim can't handle arbitrary commands")
    def test_GIVEN_an_arbitrary_command_THEN_get_a_response(self):
        self.ca.set_pv_value("ARBITRARY:SP", "?ver")
        self.ca.assert_that_pv_is("ARBITRARY", "<EMULATED FURNACE\r\n<EMULATED FURNACE\r\n")

    @parameterized.expand(parameterized_list(SAMPLE_HOLDER_MATERIALS))
    def test_GIVEN_sample_holder_material_is_set_THEN_sample_holder_material_can_be_read_back(self, _, material):
        self.ca.assert_setting_setpoint_sets_readback(material, "SAMPLEHOLDER")
