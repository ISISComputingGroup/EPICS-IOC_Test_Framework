import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list
import os


# These definitions should match self.channels in the emulator
TEMP_CARDS = ["MB0", "DB2"]
PRESSURE_CARDS = ["DB5"]
LEVEL_CARDS = ["DB8"]


def get_card_pv_prefix(card):
    """
    Given a card (e.g. "MB0", "DB1"), get the PV prefix in the IOC for it.

    Args:
        card (str): the card

    Returns:
        The pv prefix e.g. "1", "LEVEL2", "PRESSURE3"
    """
    if card in TEMP_CARDS:
        assert card not in PRESSURE_CARDS and card not in LEVEL_CARDS
        return "{}".format(TEMP_CARDS.index(card) + 1)  # Only a numeric prefix for temperature cards
    elif card in PRESSURE_CARDS:
        assert card not in LEVEL_CARDS
        return "PRESSURE:{}".format(PRESSURE_CARDS.index(card) + 1)
    elif card in LEVEL_CARDS:
        return "LEVEL:{}".format(LEVEL_CARDS.index(card) + 1)
    else:
        raise ValueError("Unknown card")


macros = {}
macros.update({"TEMP_{}".format(key): val for key, val in enumerate(TEMP_CARDS, start=1)})
macros.update({"PRESSURE_{}".format(key): val for key, val in enumerate(PRESSURE_CARDS, start=1)})
macros.update({"LEVEL_{}".format(key): val for key, val in enumerate(LEVEL_CARDS, start=1)})


DEVICE_PREFIX = "MERCURY_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "MERCURY_ITC", "iocBoot", "iocMERCURY-IOC-01"),
        "emulator": "mercuryitc",
        "macros": macros
    },
]


TEST_MODES = [TestModes.DEVSIM]


PID_PARAMS = ["P", "I", "D"]
PID_TEST_VALUES = [0.01, 99.99]
TEMPERATURE_TEST_VALUES = [0.01, 999.9999]
RESISTANCE_TEST_VALUES = TEMPERATURE_TEST_VALUES
GAS_FLOW_TEST_VALUES = TEMPERATURE_TEST_VALUES
HEATER_PERCENT_TEST_VALUES = PID_TEST_VALUES
GAS_LEVEL_TEST_VALUES = PID_TEST_VALUES

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

    @parameterized.expand(parameterized_list(
        itertools.product(PID_PARAMS, PID_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_pid_params_set_via_backdoor_THEN_readback_updates(self, _, param, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, param.lower(), test_value])
        self.ca.assert_that_pv_is("{}:{}".format(card_pv_prefix, param), test_value)

    @parameterized.expand(parameterized_list(
        itertools.product(PID_PARAMS, PID_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_pid_params_set_THEN_readback_updates(self, _, param, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        
        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            readback_pv="{}:{}".format(card_pv_prefix, param),
            set_point_pv="{}:{}:SP".format(card_pv_prefix, param))

    @parameterized.expand(parameterized_list(itertools.product(AUTOPID_MODES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_autopid_set_THEN_readback_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        
        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            readback_pv="{}:PID:AUTO".format(card_pv_prefix),
            set_point_pv="{}:PID:AUTO:SP".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, TEMP_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_actual_temp_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "temperature", test_value])
        self.ca.assert_that_pv_is("{}:TEMP".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_actual_pressure_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "pressure", test_value])
        self.ca.assert_that_pv_is("{}:PRESSURE".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(itertools.product(RESISTANCE_TEST_VALUES, TEMP_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_resistance_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "resistance", test_value])
        self.ca.assert_that_pv_is("{}:RESISTANCE".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(itertools.product(RESISTANCE_TEST_VALUES, PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_voltage_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "voltage", test_value])
        self.ca.assert_that_pv_is("{}:VOLT".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, TEMP_CARDS)))
    def test_WHEN_sp_temp_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            set_point_pv="{}:TEMP:SP".format(card_pv_prefix),
            readback_pv="{}:TEMP:SP:RBV".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, PRESSURE_CARDS)))
    def test_WHEN_sp_pressure_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            set_point_pv="{}:PRESSURE:SP".format(card_pv_prefix),
            readback_pv="{}:PRESSURE:SP:RBV".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(HEATER_MODES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_heater_mode_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="{}:HEATER:MODE:SP".format(card_pv_prefix),
            readback_pv="{}:HEATER:MODE".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(GAS_FLOW_MODES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_gas_flow_mode_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)
        
        self.ca.assert_setting_setpoint_sets_readback(
            mode,
            set_point_pv="{}:FLOW:STAT:SP".format(card_pv_prefix),
            readback_pv="{}:FLOW:STAT".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(GAS_FLOW_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_gas_flow_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="{}:FLOW:SP".format(card_pv_prefix), readback_pv="{}:FLOW".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(
        itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_heater_percent_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="{}:HEATER:SP".format(card_pv_prefix), readback_pv="{}:HEATER".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(
        itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_heater_voltage_limit_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode, set_point_pv="{}:HEATER:VOLT_LIMIT:SP".format(card_pv_prefix),
            readback_pv="{}:HEATER:VOLT_LIMIT".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(
        itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_power_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "power", test_value])
        self.ca.assert_that_pv_is("{}:HEATER:POWER".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(
        itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_curr_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "current", test_value])
        self.ca.assert_that_pv_is("{}:HEATER:CURR".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(
        itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_voltage_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage", test_value])
        self.ca.assert_that_pv_is("{}:HEATER:VOLT".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(
        itertools.product(MOCK_NICKNAMES, TEMP_CARDS + PRESSURE_CARDS + LEVEL_CARDS)))
    def test_WHEN_name_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value, readback_pv="{}:NAME".format(card_pv_prefix), set_point_pv="{}:NAME:SP".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(GAS_LEVEL_TEST_VALUES, LEVEL_CARDS)))
    def test_WHEN_helium_level_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "helium_level", test_value])
        self.ca.assert_that_pv_is_number("{}:HELIUM".format(card_pv_prefix), test_value, tolerance=0.01)

    @parameterized.expand(parameterized_list(itertools.product(GAS_LEVEL_TEST_VALUES, LEVEL_CARDS)))
    def test_WHEN_nitrogen_level_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "nitrogen_level", test_value])
        self.ca.assert_that_pv_is_number("{}:NITROGEN".format(card_pv_prefix), test_value, tolerance=0.01)
