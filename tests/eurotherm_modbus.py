import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from common_tests.eurotherm import EurothermBaseTests, PID_TEST_VALUES

from utils.testing import parameterized_list, ManagerMode

DEVICE = "EUROTHRM_01"
EMULATOR = "eurotherm"

IOCS = [
    {
        "name": DEVICE,
        "directory": get_default_ioc_dir("EUROTHRM"),
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "COMMS_MODE": "modbus",
            "ADDR_1": "01",
            "ADDR_2": "",
            "ADDR_3": "",
            "ADDR_4": "",
            "ADDR_5": "",
            "ADDR_6": "",
            "ADDR_7": "",
            "ADDR_8": "",
            "ADDR_9": "",
            "ADDR_10": "",
            "TEMP_SCALING_1": "0.1",
            "P_SCALING_1": "1",
            "I_SCALING_1": "1",
            "D_SCALING_1": "1",
            "OUTPUT_SCALING_1": "0.1",
            "NEEDLE_VALVE": "no"
        },
        "emulator": EMULATOR,
        "lewis_protocol": "eurotherm_modbus",
    },
    {
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER"
    }
]

NEEDLE_VALVE_MACROS = {
        "COMMS_MODE": "modbus",
        "ADDR_1": "01",
        "ADDR_2": "",
        "ADDR_3": "",
        "ADDR_4": "",
        "ADDR_5": "",
        "ADDR_6": "",
        "ADDR_7": "",
        "ADDR_8": "",
        "ADDR_9": "",
        "ADDR_10": "",
        "TEMP_SCALING_1": "0.01",
        "P_SCALING_1": "1",
        "I_SCALING_1": "1",
        "D_SCALING_1": "1",
        "OUTPUT_SCALING_1": "0.01",
        "NEEDLE_VALVE": "yes"
}


TEST_MODES = [TestModes.DEVSIM]


class EurothermModbusTests(EurothermBaseTests, unittest.TestCase):
    def test_WHEN_autotune_set_THEN_readback_updates(self):
        for state in [0, 1]:
            self.ca.set_pv_value("A01:AUTOTUNE:SP", state)
            self.ca.assert_that_pv_is("A01:AUTOTUNE", state)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    def test_WHEN_p_set_THEN_p_updates(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(value=val, readback_pv="A01:P", timeout=15)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    def test_WHEN_i_set_THEN_i_updates(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(value=val, readback_pv="A01:I", timeout=15)

    @parameterized.expand(parameterized_list(PID_TEST_VALUES))
    def test_WHEN_d_set_THEN_d_updates(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(value=val, readback_pv="A01:D", timeout=15)

    @parameterized.expand(parameterized_list([0, 0.5, 100]))
    def test_WHEN_max_output_set_THEN_max_output_updates(self, _, val):
        self.ca.assert_setting_setpoint_sets_readback(value=val, readback_pv="A01:MAX_OUTPUT", timeout=15)
        
    @parameterized.expand(parameterized_list([350, 250, 1000]))
    def test_GIVEN_needle_valve_manger_mode_WHEN_temp_set_too_high_THEN_temp_capped_at_320(self, _, val):
        macros = NEEDLE_VALVE_MACROS
        adjusted_temp = val
        if val > 320:
            adjusted_temp = 320
        else:
            adjusted_temp = val
        with ManagerMode(self.ca_no_prefix):
            with self._ioc.start_with_macros(macros, pv_to_wait_for="A01:TEMP:SP"):
                self.ca.set_pv_value("A01:TEMP:SP", val)
                self.ca.assert_that_pv_is("A01:TEMP:SP", adjusted_temp)

    @parameterized.expand(parameterized_list([40.2, 0.3, 105.6]))
    def test_GIVEN_needle_valve_manager_mode_WHEN_temp_set_THEN_scaling_is_correct(self, _, val):
        macros = NEEDLE_VALVE_MACROS

        with ManagerMode(self.ca_no_prefix):
            with self._ioc.start_with_macros(macros, pv_to_wait_for="A01:TEMP:SP"):
                self.ca.set_pv_value("A01:TEMP:SP", val)
                self.ca.assert_that_pv_is("A01:TEMP:SP", val)
        