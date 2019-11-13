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

MIMIC_SOLENOID_VALVES_NUMBERS = [1, 2, 4]

MIMIC_SOLENOID_VALVES_NUMBERS = [1, 2]


class IceFridgeTests(unittest.TestCase):
    """
    Tests for the IceFrdge IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_run_function_on_device("reset")

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_auto_setpoint_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(0.1, "AUTO:TEMP:SP:RBV", "AUTO:TEMP:SP")

    def test_WHEN_auto_setpoint_THEN_temperature_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(0.2, "AUTO:TEMP", "AUTO:TEMP:SP")

    def test_WHEN_manual_setpoint_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(0.3, "MANUAL:TEMP:SP:RBV", "MANUAL:TEMP:SP")

    def test_WHEN_manual_setpoint_THEN_temperature_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(0.4, "MANUAL:TEMP", "MANUAL:TEMP:SP")

    @parameterized.expand(parameterized_list(VTI_TEMP_SUFFIXES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_VTI_temp_set_backdoor_THEN_ioc_read_correctly(self, _, temp_num):
        self._lewis.backdoor_set_on_device("vti_temp{}".format(temp_num), 3.6)
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

    def test_WHEN_Lakeshore_MC_proportional_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(0.9, "LS:MC:P", "LS:MC:P:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Lakeshore_MC_integral_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1.1, "LS:MC:I", "LS:MC:I:SP")

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Lakeshore_MC_derivative_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1.2, "LS:MC:D", "LS:MC:D:SP")

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
    def test_WHEN_Mimic_pressure_set_backdoor_THEN_ioc_read_correctly(self, _, pressure_num):
        self._lewis.backdoor_run_function_on_device("set_mimic_pressure", (pressure_num, 1.4))
        self.ca.assert_that_pv_is_number("MIMIC:PRESSURE{}".format(pressure_num), 1.4, 0.001)

    @parameterized.expand(parameterized_list(MIMIC_VALVE_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Mimic_valve_status_open_THEN_readback_identical(self, _, valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "MIMIC:V{}".format(valve_num),
                                                      "MIMIC:V{}:SP".format(valve_num))

    @parameterized.expand(parameterized_list(MIMIC_VALVE_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Mimic_valve_status_closed_THEN_readback_identical(self, _, valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "MIMIC:V{}".format(valve_num),
                                                      "MIMIC:V{}:SP".format(valve_num))

        self.ca.assert_setting_setpoint_sets_readback("CLOSED", "MIMIC:V{}".format(valve_num),
                                                      "MIMIC:V{}:SP".format(valve_num))

    @parameterized.expand(parameterized_list(MIMIC_SOLENOID_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Mimic_proportional_valve_THEN_readback_identical(self, _, proportional_valve_num):
        self.ca.assert_setting_setpoint_sets_readback(1.5, "MIMIC:PV{}".format(proportional_valve_num),
                                                      "MIMIC:PV{}:SP".format(proportional_valve_num))

    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Mimic_needle_valve_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1.6, "MIMIC:NV", "MIMIC:NV:SP")

    @parameterized.expand(parameterized_list(MIMIC_SOLENOID_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Mimic_solenoid_valve_open_THEN_readback_identical(self, _, solenoid_valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "MIMIC:SV{}".format(solenoid_valve_num),
                                                      "MIMIC:SV{}:SP".format(solenoid_valve_num))

    @parameterized.expand(parameterized_list(MIMIC_SOLENOID_VALVES_NUMBERS))
    @skip_if_recsim("pv updated when other pv processes, has no scan field")
    def test_WHEN_Mimic_solenoid_valve_close_THEN_readback_identical(self, _, solenoid_valve_num):
        self.ca.assert_setting_setpoint_sets_readback("OPEN", "MIMIC:SV{}".format(solenoid_valve_num),
                                                      "MIMIC:SV{}:SP".format(solenoid_valve_num))

        self.ca.assert_setting_setpoint_sets_readback("CLOSED", "MIMIC:SV{}".format(solenoid_valve_num),
                                                      "MIMIC:SV{}:SP".format(solenoid_valve_num))

    @skip_if_recsim("lewis backdoor not available in recsim")
    def test_WHEN_Mimic_1K_stage_THEN_readback_identical(self):
        self._lewis.backdoor_set_on_device("mimic_1K_stage", 1.7)
        self.ca.assert_that_pv_is_number("MIMIC:1K", 1.7, 0.001)
