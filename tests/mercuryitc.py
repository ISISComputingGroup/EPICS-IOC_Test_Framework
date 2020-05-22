import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list
import os


DEVICE_PREFIX = "MERCURY_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "MERCURY_ITC", "iocBoot", "iocMERCURY-IOC-01"),
        "emulator": "mercuryitc",
        "macros": {
            "VI_TEMP_1": "1"
        }
    },
]


TEST_MODES = [TestModes.DEVSIM]


PID_PARAMS = ["P", "I", "D"]
PID_TEST_VALUES = [0.0, 0.01, 99.99]
TEMPERATURE_TEST_VALUES = [0.0, 0.01, 999.9999]
RESISTANCE_TEST_VALUES = TEMPERATURE_TEST_VALUES
GAS_FLOW_TEST_VALUES = TEMPERATURE_TEST_VALUES
HEATER_PERCENT_TEST_VALUES = PID_TEST_VALUES

PRIMARY_TEMPERATURE_CHANNEL = "MB0"

HEATER_MODES = ["Auto", "Manual"]
GAS_FLOW_MODES = ["Auto", "Manual"]
AUTOPID_MODES = ["OFF", "ON"]

MOCK_NICKNAMES = ["MyNickName", "SomeOtherNickname"]


class MercuryTests(unittest.TestCase):
    """
    Tests for the Mercury IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("mercuryitc", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(itertools.product(PID_PARAMS, PID_TEST_VALUES)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_pid_params_set_via_backdoor_THEN_readback_updates(self, _, param, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [PRIMARY_TEMPERATURE_CHANNEL, param.lower(), test_value])
        self.ca.assert_that_pv_is("1:{}".format(param), test_value)

    @parameterized.expand(parameterized_list(itertools.product(PID_PARAMS, PID_TEST_VALUES)))
    def test_WHEN_pid_params_set_THEN_readback_updates(self, _, param, test_value):
        self.ca.assert_setting_setpoint_sets_readback(
            test_value, readback_pv="1:{}".format(param), set_point_pv="1:{}:SP".format(param))

    @parameterized.expand(parameterized_list(AUTOPID_MODES))
    def test_WHEN_autopid_set_THEN_readback_updates(self, _, test_value):
        self.ca.assert_setting_setpoint_sets_readback(
            test_value, readback_pv="1:PID:AUTO", set_point_pv="1:PID:AUTO:SP")

    @parameterized.expand(parameterized_list(TEMPERATURE_TEST_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_actual_temp_is_set_via_backdoor_THEN_pv_updates(self, _, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [PRIMARY_TEMPERATURE_CHANNEL, "temperature", test_value])
        self.ca.assert_that_pv_is("1:TEMP", test_value)

    @parameterized.expand(parameterized_list(RESISTANCE_TEST_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_resistance_is_set_via_backdoor_THEN_pv_updates(self, _, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [PRIMARY_TEMPERATURE_CHANNEL, "resistance", test_value])
        self.ca.assert_that_pv_is("1:RESISTANCE", test_value)

    @parameterized.expand(parameterized_list(TEMPERATURE_TEST_VALUES))
    def test_WHEN_sp_temp_is_set_THEN_pv_updates(self, _, test_value):
        self.ca.assert_setting_setpoint_sets_readback(test_value, set_point_pv="1:TEMP:SP", readback_pv="1:TEMP:SP:RBV")

    @parameterized.expand(parameterized_list(HEATER_MODES))
    def test_WHEN_heater_mode_is_set_THEN_pv_updates(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="1:HEATER:MODE:SP", readback_pv="1:HEATER:MODE")

    @parameterized.expand(parameterized_list(GAS_FLOW_MODES))
    def test_WHEN_gas_flow_mode_is_set_THEN_pv_updates(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="1:FLOW:STAT:SP", readback_pv="1:FLOW:STAT")

    @parameterized.expand(parameterized_list(GAS_FLOW_TEST_VALUES))
    def test_WHEN_gas_flow_is_set_THEN_pv_updates(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="1:FLOW:SP", readback_pv="1:FLOW")

    @parameterized.expand(parameterized_list(HEATER_PERCENT_TEST_VALUES))
    def test_WHEN_heater_percent_is_set_THEN_pv_updates(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="1:HEATER:SP", readback_pv="1:HEATER")

    @parameterized.expand(parameterized_list(HEATER_PERCENT_TEST_VALUES))
    def test_WHEN_heater_voltage_limit_is_set_THEN_pv_updates(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="1:HEATER:VOLT_LIMIT:SP", readback_pv="1:HEATER:VOLT_LIMIT")

    @parameterized.expand(parameterized_list(HEATER_PERCENT_TEST_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_power_is_set_via_backdoor_THEN_pv_updates(self, _, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", ["DB0", "power", test_value])  # TODO: refactor DB0
        self.ca.assert_that_pv_is("1:HEATER:POWER", test_value)

    @parameterized.expand(parameterized_list(HEATER_PERCENT_TEST_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_curr_is_set_via_backdoor_THEN_pv_updates(self, _, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", ["DB0", "current", test_value])  # TODO: refactor DB0
        self.ca.assert_that_pv_is("1:HEATER:CURR", test_value)

    @parameterized.expand(parameterized_list(HEATER_PERCENT_TEST_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_voltage_is_set_via_backdoor_THEN_pv_updates(self, _, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", ["DB0", "voltage", test_value])  # TODO: refactor DB0
        self.ca.assert_that_pv_is("1:HEATER:VOLT", test_value)

    @parameterized.expand(parameterized_list(MOCK_NICKNAMES))
    def test_WHEN_name_is_set__THEN_pv_updates(self, _, test_value):
        self.ca.assert_setting_setpoint_sets_readback(test_value, readback_pv="1:NAME", set_point_pv="1:NAME:SP")
