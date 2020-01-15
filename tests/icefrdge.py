import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "ICEFRDGE_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ICEFRDGE"),
        "macros": {},
        "emulator": "icefrdge",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

VTI_TEMP_SUFFIXES = [1, 2, 3, 4]

VTI_LOOPS = [1, 2]

VTI_LOOP_TEST_INPUTS = [0, 0.001, 0.333, 273]

LS_MC_HTR_RANGE_VALUES = ["Off", "31.6 uA", "100 uA", "316 uA", "1.00 mA", "3.16 mA", "10 mA", "31.6 mA", "100 mA"]

LS_MC_HTR_RANGE_INVALID_VALUES = [-3, -1, 4.5, 9, 14]

LS_VOLTAGE_RANGE_VALUES = ["2.00 uV", "6.32 uV", "20 uV", "63.2 uV", "200 uV", "632 uV", "2.00 mV", "6.32 mV",
                           "20.0 mV", "63.2 mV", "200 mV", "632 mV"]

LS_VOLTAGE_CHANNELS = [5, 6]

LS_VOLTAGE_RANGE_INVALID_VALUES = [-3, 0, 6.3, 13, 17]

MIMIC_PRESSURE_SUFFIXES = [1, 2, 3, 4]

MIMIC_VALVE_NUMBERS = [(i + 1) for i in range(10)]

MIMIC_PROPORTIONAL_VALVES_NUMBERS = [1, 2, 4]

MIMIC_SOLENOID_VALVES_NUMBERS = [1, 2]

TEST_ALARM_STATUS_PVS = ["VTI:TEMP1", "VTI:TEMP2", "VTI:TEMP3", "VTI:TEMP4", "VTI:LOOP1:TSET", "VTI:LOOP2:TSET",
                         "VTI:LOOP1:P", "VTI:LOOP2:P", "VTI:LOOP1:I", "VTI:LOOP2:I", "VTI:LOOP1:D", "VTI:LOOP2:D",
                         "VTI:LOOP1:RAMPRATE", "VTI:LOOP2:RAMPRATE", "LS:MC:CERNOX", "LS:MC:RUO",
                         "LS:STILL:TEMP", "LS:MC:TEMP", "LS:MC:P", "LS:MC:I", "LS:MC:D", "LS:MC:HTR:RANGE",
                         "LS:MC:HTR:PERCENT", "LS:STILL", "LS:VLTG:RANGE:CH5", "LS:VLTG:RANGE:CH6", "PRESSURE1",
                         "PRESSURE2", "PRESSURE3", "PRESSURE4", "VALVE1", "VALVE2", "VALVE3",
                         "VALVE4", "VALVE5", "VALVE6", "VALVE7", "VALVE8", "VALVE9", "VALVE10",
                         "SOLENOID_VALVE1", "SOLENOID_VALVE2", "PROPORTIONAL_VALVE1", "PROPORTIONAL_VALVE2",
                         "PROPORTIONAL_VALVE4", "NEEDLE_VALVE", "1K:TEMP", "MC:TEMP", "MC:RESISTANCE:CALC",
                         "MIMIC:SEQUENCE:TEMP", "MIMIC:INFO", "STATE", "NVMODE", "1K:PUMP", "HE3:PUMP", "ROOTS"]


class IceFridgeTests(unittest.TestCase):
    """
    Tests for the IceFrdge IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=25)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_run_function_on_device("reset")
            self._lewis.backdoor_set_on_device("connected", True)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(VTI_TEMP_SUFFIXES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_VTI_temp_set_backdoor_THEN_ioc_read_correctly(self, _, temp_num):
        self._lewis.backdoor_run_function_on_device("set_cryo_temp", (temp_num, 3.6))
        self.ca.assert_that_pv_is_number("VTI:TEMP{}".format(temp_num), 3.6, 0.001)

    @parameterized.expand(parameterized_list(itertools.product(VTI_LOOPS, VTI_LOOP_TEST_INPUTS)))
    def test_WHEN_vti_loop_setpoint_THEN_readback_identical(self, _, loop_num, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "VTI:LOOP{}:TSET".format(loop_num),
                                                      "VTI:LOOP{}:TSET:SP".format(loop_num))

    @parameterized.expand(parameterized_list(itertools.product(VTI_LOOPS, VTI_LOOP_TEST_INPUTS)))
    def test_WHEN_vti_loop_proportional_THEN_readback_identical(self, _, loop_num, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "VTI:LOOP{}:P".format(loop_num),
                                                      "VTI:LOOP{}:P:SP".format(loop_num))

    @parameterized.expand(parameterized_list(itertools.product(VTI_LOOPS, VTI_LOOP_TEST_INPUTS)))
    def test_WHEN_vti_loop_integral_THEN_readback_identical(self, _, loop_num, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "VTI:LOOP{}:I".format(loop_num),
                                                      "VTI:LOOP{}:I:SP".format(loop_num))

    @parameterized.expand(parameterized_list(itertools.product(VTI_LOOPS, VTI_LOOP_TEST_INPUTS)))
    def test_WHEN_vti_loop_derivative_THEN_readback_identical(self, _, loop_num, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "VTI:LOOP{}:D".format(loop_num),
                                                      "VTI:LOOP{}:D:SP".format(loop_num))

    @parameterized.expand(parameterized_list(itertools.product(VTI_LOOPS, VTI_LOOP_TEST_INPUTS)))
    def test_WHEN_vti_loop_ramp_rate_THEN_readback_identical(self, _, loop_num, temp):
        self.ca.assert_setting_setpoint_sets_readback(temp, "VTI:LOOP{}:RAMPRATE".format(loop_num),
                                                      "VTI:LOOP{}:RAMPRATE:SP".format(loop_num))

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_MC_Cernox_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("lakeshore_mc_cernox", 0.5)
        self.ca.assert_that_pv_is_number("LS:MC:CERNOX", 0.5, 0.001)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_MC_RuO_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("lakeshore_mc_ruo", 0.6)
        self.ca.assert_that_pv_is_number("LS:MC:RUO", 0.6, 0.001)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_still_temp_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("lakeshore_still_temp", 0.7)
        self.ca.assert_that_pv_is_number("LS:STILL:TEMP", 0.7, 0.001)

    def test_WHEN_Lakeshore_MC_setpoint_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(0.8, "LS:MC:TEMP", "LS:MC:TEMP:SP")

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_Lakeshore_MC_setpoint_is_zero_THEN_scan_correct(self):
        self.ca.set_pv_value("LS:MC:TEMP:SP", 0)
        self._lewis.assert_that_emulator_value_is("lakeshore_scan", "1", 15)
        self._lewis.assert_that_emulator_value_is("lakeshore_cmode", "4", 15)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_Lakeshore_MC_setpoint_is_larger_than_zero_THEN_scan_correct(self):
        self.ca.set_pv_value("LS:MC:TEMP:SP", 4)
        self._lewis.assert_that_emulator_value_is("lakeshore_scan", "0", 15)
        self._lewis.assert_that_emulator_value_is("lakeshore_cmode", "1", 15)

    def test_WHEN_Lakeshore_MC_setpoint_negative_THEN_readback_zero(self):
        self.ca.set_pv_value("LS:MC:TEMP:SP", -1)

        self.ca.assert_that_pv_is("LS:MC:TEMP", 0)

    def test_WHEN_Lakeshore_MC_setpoint_over_limit_THEN_readback_at_limit(self):
        self.ca.set_pv_value("LS:MC:TEMP:SP", 301)

        self.ca.assert_that_pv_is("LS:MC:TEMP", 300)

    def test_WHEN_Lakeshore_MC_proportional_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(0.9, "LS:MC:P", "LS:MC:P:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Lakeshore_MC_integral_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(11, "LS:MC:I", "LS:MC:I:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Lakeshore_MC_derivative_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(12, "LS:MC:D", "LS:MC:D:SP")

    @parameterized.expand(parameterized_list(LS_MC_HTR_RANGE_VALUES))
    def test_WHEN_Lakeshore_MC_heater_range_THEN_readback_identical(self, _, heater_range):
        self.ca.assert_setting_setpoint_sets_readback(heater_range, "LS:MC:HTR:RANGE", "LS:MC:HTR:RANGE:SP")

    @parameterized.expand(parameterized_list(LS_MC_HTR_RANGE_INVALID_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_lakeshore_MC_heater_range_invalid_setpoint_THEN_pv_in_alarm(self, _, invalid_range):
        self.ca.assert_that_pv_alarm_is("LS:MC:HTR:RANGE", self.ca.Alarms.NONE, timeout=15)

        self._lewis.backdoor_set_on_device("lakeshore_mc_heater_range", invalid_range)
        self.ca.assert_that_pv_alarm_is("LS:MC:HTR:RANGE", self.ca.Alarms.INVALID, timeout=15)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_MC_heater_percentage_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("lakeshore_mc_heater_percentage", 50)
        self.ca.assert_that_pv_is_number("LS:MC:HTR:PERCENT", 50, 0.001)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_MC_still_output_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("lakeshore_still_output", 1.3)
        self.ca.assert_that_pv_is_number("LS:STILL", 1.3, 0.001)

    @parameterized.expand(parameterized_list(itertools.product(LS_VOLTAGE_CHANNELS, LS_VOLTAGE_RANGE_VALUES)))
    def test_WHEN_Lakeshore_voltage_range_THEN_readback_identical(self, _, voltage_channel, voltage_value):
        self.ca.assert_setting_setpoint_sets_readback(voltage_value, "LS:VLTG:RANGE:CH{}".format(voltage_channel),
                                                      "LS:VLTG:RANGE:SP")

    @parameterized.expand(parameterized_list(itertools.product(LS_VOLTAGE_CHANNELS, LS_VOLTAGE_RANGE_INVALID_VALUES)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_voltage_range_invalid_setpoint_THEN_pv_in_alarm(self, _, voltage_channel, invalid_range):
        self.ca.assert_that_pv_alarm_is("LS:VLTG:RANGE:CH{}".format(voltage_channel), self.ca.Alarms.NONE,
                                        timeout=15)

        self._lewis.backdoor_set_on_device("lakeshore_exc_voltage_range_ch{}".format(voltage_channel), invalid_range)
        self.ca.assert_that_pv_alarm_is("LS:VLTG:RANGE:CH{}".format(voltage_channel), self.ca.Alarms.INVALID,
                                        timeout=15)

    @parameterized.expand(parameterized_list(MIMIC_PRESSURE_SUFFIXES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_pressure_set_backdoor_THEN_ioc_read_correctly(self, _, pressure_num):
        self._lewis.backdoor_run_function_on_device("set_pressure", (pressure_num, 1.4))
        self.ca.assert_that_pv_is_number("PRESSURE{}".format(pressure_num), 1.4, 0.001)

    @parameterized.expand(parameterized_list(MIMIC_VALVE_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_valve_status_open_THEN_readback_identical(self, _, valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "VALVE{}".format(valve_num),
                                                      "VALVE{}:SP".format(valve_num))

    @parameterized.expand(parameterized_list(MIMIC_VALVE_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_valve_status_closed_THEN_readback_identical(self, _, valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "VALVE{}".format(valve_num),
                                                      "VALVE{}:SP".format(valve_num))

        self.ca.assert_setting_setpoint_sets_readback("CLOSED", "VALVE{}".format(valve_num),
                                                      "VALVE{}:SP".format(valve_num))

    @parameterized.expand(parameterized_list(MIMIC_PROPORTIONAL_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_proportional_valve_THEN_readback_identical(self, _, proportional_valve_num):
        self.ca.assert_setting_setpoint_sets_readback(1.5, "PROPORTIONAL_VALVE{}".format(proportional_valve_num),
                                                      "PROPORTIONAL_VALVE{}:SP".format(proportional_valve_num))

    @parameterized.expand(parameterized_list(itertools.product(MIMIC_PROPORTIONAL_VALVES_NUMBERS, [0.001, 2])))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_proportional_valve_not_0_THEN_calc_is_one(self, _, proportional_valve_num, test_value):
        self.ca.set_pv_value("PROPORTIONAL_VALVE{}:SP".format(proportional_valve_num), test_value)

        self.ca.assert_that_pv_is("PROPORTIONAL_VALVE{}:_CALC".format(proportional_valve_num), 1)

    @parameterized.expand(parameterized_list(MIMIC_PROPORTIONAL_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_proportional_valve_0_THEN_calc_is_zero(self, _, proportional_valve_num):
        self.ca.set_pv_value("PROPORTIONAL_VALVE{}:SP".format(proportional_valve_num), 1)
        self.ca.assert_that_pv_is("PROPORTIONAL_VALVE{}:_CALC".format(proportional_valve_num), 1)

        self.ca.set_pv_value("PROPORTIONAL_VALVE{}:SP".format(proportional_valve_num), 0)
        self.ca.assert_that_pv_is("PROPORTIONAL_VALVE{}:_CALC".format(proportional_valve_num), 0)

    @parameterized.expand(parameterized_list(MIMIC_PROPORTIONAL_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_proportional_valve_sp_negative_THEN_readback_zero(self, _, proportional_valve_num):
        self.ca.set_pv_value("PROPORTIONAL_VALVE{}:SP".format(proportional_valve_num), -1)

        self.ca.assert_that_pv_is("PROPORTIONAL_VALVE{}".format(proportional_valve_num), 0)

    @parameterized.expand(parameterized_list(MIMIC_PROPORTIONAL_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_proportional_valve_sp_over_limit_THEN_readback_at_limit(self, _, proportional_valve_num):
        self.ca.set_pv_value("PROPORTIONAL_VALVE{}:SP".format(proportional_valve_num), 101)

        self.ca.assert_that_pv_is("PROPORTIONAL_VALVE{}".format(proportional_valve_num), 100)

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_needle_valve_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1.6, "NEEDLE_VALVE", "NEEDLE_VALVE:SP")

    @parameterized.expand(parameterized_list([0.001, 2]))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_needle_valve_not_0_THEN_calc_is_one(self, _, test_value):
        self.ca.set_pv_value("NEEDLE_VALVE:SP", test_value)
        self.ca.assert_that_pv_is("NEEDLE_VALVE:_CALC", 1)

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_needle_valve_0_THEN_calc_is_zero(self):
        self.ca.set_pv_value("NEEDLE_VALVE:SP", 0)
        self.ca.assert_that_pv_is("NEEDLE_VALVE:_CALC", 0)

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_needle_valve_sp_negative_THEN_readback_zero(self):
        self.ca.set_pv_value("NEEDLE_VALVE:SP", -1)

        self.ca.assert_that_pv_is("NEEDLE_VALVE", 0)

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_needle_valve_sp_over_limit_THEN_readback_at_limit(self):
        self.ca.set_pv_value("NEEDLE_VALVE:SP", 101)

        self.ca.assert_that_pv_is("NEEDLE_VALVE", 100)

    @parameterized.expand(parameterized_list(MIMIC_SOLENOID_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_solenoid_valve_open_THEN_readback_identical(self, _, solenoid_valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "SOLENOID_VALVE{}".format(solenoid_valve_num),
                                                      "SOLENOID_VALVE{}:SP".format(solenoid_valve_num))

    @parameterized.expand(parameterized_list(MIMIC_SOLENOID_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_solenoid_valve_close_THEN_readback_identical(self, _, solenoid_valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "SOLENOID_VALVE{}".format(solenoid_valve_num),
                                                      "SOLENOID_VALVE{}:SP".format(solenoid_valve_num))

        self.ca.assert_setting_setpoint_sets_readback("CLOSED", "SOLENOID_VALVE{}".format(solenoid_valve_num),
                                                      "SOLENOID_VALVE{}:SP".format(solenoid_valve_num))

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_1K_stage_temp_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("temp_1K_stage", 1.7)
        self.ca.assert_that_pv_is_number("1K:TEMP", 1.7, 0.001)

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_MC_temperature_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("mixing_chamber_temp", 1.8)
        self.ca.assert_that_pv_is_number("MC:TEMP", 1.8, 0.001)

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_MC_resistance_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("mixing_chamber_resistance", 1.9)
        self.ca.assert_that_pv_is_number("MC:_RESISTANCE", 1.9, 0.001)

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_MC_resistance_calc_THEN_calculation_correct(self):
        self._lewis.backdoor_set_on_device("mixing_chamber_resistance", 1918)
        self.ca.assert_that_pv_is_number("MC:RESISTANCE:CALC", 1.918, 0.001)

    def test_WHEN_mimic_mode_manual_THEN_buttons_disabled(self):
        self.ca.set_pv_value("MIMIC:MODE:SP", "MANUAL")

        self.ca.assert_that_pv_is("MIMIC:START:SP.DISP", '1')
        self.ca.assert_that_pv_is("MIMIC:SKIP:SP.DISP", '1')
        self.ca.assert_that_pv_is("MIMIC:STOP:SP.DISP", '1')

    def test_WHEN_mimic_mode_automatic_THEN_buttons_disabled(self):
        self.ca.set_pv_value("MIMIC:MODE:SP", "AUTOMATIC")

        self.ca.assert_that_pv_is("MIMIC:START:SP.DISP", '1')
        self.ca.assert_that_pv_is("MIMIC:SKIP:SP.DISP", '1')
        self.ca.assert_that_pv_is("MIMIC:STOP:SP.DISP", '1')

    def test_WHEN_mimic_mode_semi_automatic_THEN_buttons_enabled(self):
        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")

        self.ca.assert_that_pv_is("MIMIC:START:SP.DISP", '0')
        self.ca.assert_that_pv_is("MIMIC:SKIP:SP.DISP", '0')
        self.ca.assert_that_pv_is("MIMIC:STOP:SP.DISP", '0')

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_skip_THEN_skipped(self):
        self._lewis.assert_that_emulator_value_is("skipped", "False", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:SKIP:SP", "SKIP")

        self._lewis.assert_that_emulator_value_is("skipped", "True", 15)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_stop_THEN_stopped(self):
        self._lewis.assert_that_emulator_value_is("stopped", "False", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:STOP:SP", "STOP")

        self._lewis.assert_that_emulator_value_is("stopped", "True", 15)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_sequence_condense_THEN_condense(self):
        self._lewis.assert_that_emulator_value_is("condense", "False", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        self.ca.set_pv_value("MIMIC:SEQUENCE:SP", "Condense")
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:START:SP", "START")

        self._lewis.assert_that_emulator_value_is("condense", "True", 15)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_sequence_circulate_THEN_circulate(self):
        self._lewis.assert_that_emulator_value_is("circulate", "False", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        self.ca.set_pv_value("MIMIC:SEQUENCE:SP", "Circulate")
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:START:SP", "START")

        self._lewis.assert_that_emulator_value_is("circulate", "True", 15)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_sequence_condense_and_circulate_THEN_condense_and_circulate(self):
        self._lewis.assert_that_emulator_value_is("condense", "False", 15)
        self._lewis.assert_that_emulator_value_is("circulate", "False", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        self.ca.set_pv_value("MIMIC:SEQUENCE:SP", "Condense & Circulate")
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:START:SP", "START")

        self._lewis.assert_that_emulator_value_is("condense", "True", 15)
        self._lewis.assert_that_emulator_value_is("circulate", "True", 15)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_sequence_temp_control_THEN_readback_identical(self):
        self._lewis.assert_that_emulator_value_is("temp_control", "0", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        self.ca.set_pv_value("MIMIC:SEQUENCE:SP", "Temperature Control")
        self.ca.set_pv_value("MIMIC:SEQUENCE:TEMP:SP", 2.3)
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:START:SP", "START")

        self.ca.assert_that_pv_is("MIMIC:SEQUENCE:TEMP", 2.3)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_sequence_make_safe_THEN_make_safe(self):
        self._lewis.assert_that_emulator_value_is("make_safe", "False", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        self.ca.set_pv_value("MIMIC:SEQUENCE:SP", "Make Safe")
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:START:SP", "START")

        self._lewis.assert_that_emulator_value_is("make_safe", "True", 15)

    @skip_if_recsim("Lewis assertion not working in recsim")
    def test_WHEN_mimic_sequence_warm_up_THEN_warm_up(self):
        self._lewis.assert_that_emulator_value_is("warm_up", "False", 15)

        self.ca.set_pv_value("MIMIC:MODE:SP", "SEMI AUTOMATIC")
        self.ca.set_pv_value("MIMIC:SEQUENCE:SP", "Warm Up")
        # does not matter what value the pv is set to, only that it processes
        self.ca.set_pv_value("MIMIC:START:SP", "START")

        self._lewis.assert_that_emulator_value_is("warm_up", "True", 15)

    @skip_if_recsim("Lewis backdoor not working in recsim")
    def test_WHEN_mimic_info_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("mimic_info", "RBMK reactors do not explode!")
        self.ca.assert_that_pv_is("MIMIC:INFO", "RBMK reactors do not explode!")

    @skip_if_recsim("Lewis backdoor not working in recsim")
    def test_WHEN_state_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("state", "It\\'s disgraceful, really!")
        self.ca.assert_that_pv_is("STATE", "It's disgraceful, really!")

    def test_WHEN_nv_mode_setpoint_manual_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("MANUAL", "NVMODE", "NVMODE:SP")

    def test_WHEN_nv_mode_setpoint_auto_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("MANUAL", "NVMODE", "NVMODE:SP")

        self.ca.assert_setting_setpoint_sets_readback("AUTO", "NVMODE", "NVMODE:SP")

    def test_WHEN_1K_pump_off_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("ON", "1K:PUMP", "1K:PUMP:SP")

        self.ca.assert_setting_setpoint_sets_readback("OFF", "1K:PUMP", "1K:PUMP:SP")

    def test_WHEN_1K_pump_on_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("OFF", "1K:PUMP", "1K:PUMP:SP")

        self.ca.assert_setting_setpoint_sets_readback("ON", "1K:PUMP", "1K:PUMP:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_He3_pump_off_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("OFF", "HE3:PUMP", "HE3:PUMP:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_He3_pump_on_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("OFF", "HE3:PUMP", "HE3:PUMP:SP")

        self.ca.assert_setting_setpoint_sets_readback("ON", "HE3:PUMP", "HE3:PUMP:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_roots_pump_off_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("OFF", "ROOTS", "ROOTS:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_roots_pump_on_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback("OFF", "ROOTS", "ROOTS:SP")

        self.ca.assert_setting_setpoint_sets_readback("ON",  "ROOTS", "ROOTS:SP")

    @skip_if_recsim("testing lack of connection to device makes no sense in recsim")
    def test_WHEN_ioc_disconnected_THEN_all_pvs_in_alarm(self):
        for pv in TEST_ALARM_STATUS_PVS:
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

        self._lewis.backdoor_set_on_device("connected", False)

        for pv in TEST_ALARM_STATUS_PVS:
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID)
