import itertools
import unittest
from datetime import time
from time import sleep

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list, ManagerMode
import os


# These definitions should match self.channels in the emulator
TEMP_CARDS = ["MB0.T0", "DB2.T1"]
PRESSURE_CARDS = ["DB5.P0"]
LEVEL_CARDS = ["DB8.L0"]
HEATER_CARDS = ["MB1.H0", "DB3.H1", "DB6.H2"]
AUX_CARDS = ["DB1.A0", "DB4.A1", "DB7.A2"]

SPC_MIN_PRESSURE = 5.00
SPC_MAX_PRESSURE = 35.00
SPC_TEMP_DEADBAND = 2.5
SPC_GAIN = 1.5

SPC_OFFSET = 2.5
SPC_OFFSET_DURATION = 5.0 / 60.0  # make it go up 0.5 mbar a second for testing


def get_card_pv_prefix(card):
    """
    Given a card (e.g. "MB0.T1", "DB1.L1"), get the PV prefix in the IOC for it.

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
macros["FLOW_SPC_PRESSURE_1"] = 1
macros["FLOW_SPC_MIN_PRESSURE"] = SPC_MIN_PRESSURE
macros["FLOW_SPC_TEMP_DEADBAND"] = SPC_TEMP_DEADBAND
macros["FLOW_SPC_MAX_PRESSURE"] = SPC_MAX_PRESSURE
macros["FLOW_SPC_OFFSET"] = SPC_OFFSET
macros["FLOW_SPC_OFFSET_DURATION"] = SPC_OFFSET_DURATION
macros["FLOW_SPC_GAIN"] = SPC_GAIN

macros["CALIB_BASE_DIR"] = EPICS_TOP.replace("\\", "/")
macros["CALIB_DIR"] = os.path.join("support", "mercuryitc", "master", "settings").replace("\\", "/")
macros["FLOW_SPC_TABLE_FILE"] = "little_blue_cryostat.txt"

macros["VTI_SPC_PRESSURE_1"] = 1
macros["VTI_SPC_MIN_PRESSURE"] = 10
macros["VTI_SPC_MAX_PRESSURE"] = 40
macros["VTI_SPC_PRESSURE_CONSTANT"] = 5
macros["VTI_SPC_TEMP_CUTOFF_POINT"] = 5



DEVICE_PREFIX = "MERCURY_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "MERCURY_ITC", "iocBoot", "iocMERCURY-IOC-01"),
        "emulator": "mercuryitc",
        "macros": macros
    },
    {
        # INSTETC is required to enable manager mode.
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    }
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


PID_PARAMS = ["P", "I", "D"]
PID_TEST_VALUES = [0.01, 99.99]
TEMPERATURE_TEST_VALUES = [0.01, 999.9999]
RESISTANCE_TEST_VALUES = TEMPERATURE_TEST_VALUES
GAS_FLOW_TEST_VALUES = PID_TEST_VALUES
HEATER_PERCENT_TEST_VALUES = PID_TEST_VALUES
GAS_LEVEL_TEST_VALUES = PID_TEST_VALUES

PRIMARY_TEMPERATURE_CHANNEL = "MB0.T0"

HEATER_MODES = ["Auto", "Manual"]
GAS_FLOW_MODES = ["Auto", "Manual"]
AUTOPID_MODES = ["OFF", "ON"]
HELIUM_READ_RATES = ["Slow", "Fast"]

MOCK_NICKNAMES = ["MyNickName", "SomeOtherNickname"]
MOCK_CALIB_FILES = ["FakeCalib", "OtherFakeCalib", "test_calib.dat", "test space calib.dat"]

# Taken from the calibration file, minimum temperature, pressure
PRESSSURE_FOR = [(0, 35),
                 (4, 35),
                 (10, 25),
                 (20, 14),
                 (50, 10),
                 (100, 8),
                 (150, 8),
                 (200, 8),
                 (280, 8)]


def pressure_for(setpoint_temp):
    """
    For a given pressure return the base pressure
    :param setpoint_temp: set point to get pressure for
    :return: pressure
    """
    last_pressure = -10
    for temp, pressure in PRESSSURE_FOR:
        if setpoint_temp < temp:
            return last_pressure
        last_pressure = pressure
    return last_pressure


class MercuryTests(unittest.TestCase):
    """
    Tests for the Mercury IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("mercuryitc", DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("connected", True)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)
        card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        self.ca.assert_setting_setpoint_sets_readback("OFF", readback_pv="{}:SPC".format(card_pv_prefix),
                                                      expected_alarm=self.ca.Alarms.MAJOR)
        

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
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_helium_level_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "helium_level", test_value])
        self.ca.assert_that_pv_is_number("{}:HELIUM".format(card_pv_prefix), test_value, tolerance=0.01)

    @parameterized.expand(parameterized_list(itertools.product(GAS_LEVEL_TEST_VALUES, LEVEL_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_nitrogen_level_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "nitrogen_level", test_value])
        self.ca.assert_that_pv_is_number("{}:NITROGEN".format(card_pv_prefix), test_value, tolerance=0.01)

    @parameterized.expand(parameterized_list(itertools.product(TEMP_CARDS + PRESSURE_CARDS, HEATER_CARDS)))
    def test_WHEN_heater_association_is_set_THEN_pv_updates(self, _, parent_card, associated_card):
        card_pv_prefix = get_card_pv_prefix(parent_card)

        with ManagerMode(ChannelAccess()):
            self.ca.assert_setting_setpoint_sets_readback(associated_card, "{}:HTRCHAN".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(TEMP_CARDS + PRESSURE_CARDS, AUX_CARDS)))
    def test_WHEN_aux_association_is_set_THEN_pv_updates(self, _, parent_card, associated_card):
        card_pv_prefix = get_card_pv_prefix(parent_card)
        with ManagerMode(ChannelAccess()):
            self.ca.assert_setting_setpoint_sets_readback(associated_card, "{}:AUXCHAN".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(itertools.product(HELIUM_READ_RATES, LEVEL_CARDS)))
    def test_WHEN_he_read_rate_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        self.ca.assert_setting_setpoint_sets_readback(test_value, "{}:HELIUM:READ_RATE".format(card_pv_prefix))

    @parameterized.expand(parameterized_list([
        ("CATALOG:PARSE.VALA", TEMP_CARDS),
        ("CATALOG:PARSE.VALB", PRESSURE_CARDS),
        ("CATALOG:PARSE.VALC", LEVEL_CARDS),
        ("CATALOG:PARSE.VALD", HEATER_CARDS),
        ("CATALOG:PARSE.VALE", AUX_CARDS),
    ]))
    @skip_if_recsim("Complex logic not tested in recsim")
    def test_WHEN_getting_catalog_it_contains_all_cards(self, _, pv, cards):
        for card in cards:
            self.ca.assert_that_pv_value_causes_func_to_return_true(pv, lambda val: card in val)

    @parameterized.expand(parameterized_list(itertools.product(MOCK_CALIB_FILES, TEMP_CARDS + PRESSURE_CARDS)))
    def test_WHEN_setting_calibration_file_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        with ManagerMode(ChannelAccess()):
            self.ca.assert_setting_setpoint_sets_readback(test_value, "{}:CALFILE".format(card_pv_prefix))

    @parameterized.expand(parameterized_list(["O", "R"]))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_resistance_suffix_is_changed_THEN_resistance_reads_correctly(self, _, resistance_suffix):
        self._lewis.backdoor_set_on_device("resistance_suffix", resistance_suffix)
        resistance_value = 3
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [PRIMARY_TEMPERATURE_CHANNEL, "resistance", resistance_value]
        )
        self.ca.assert_that_pv_is(
            "{}:RESISTANCE".format(get_card_pv_prefix(PRIMARY_TEMPERATURE_CHANNEL)), resistance_value
        )
        self.ca.assert_that_pv_alarm_is(
            "{}:RESISTANCE".format(get_card_pv_prefix(PRIMARY_TEMPERATURE_CHANNEL)), self.ca.Alarms.NONE
        )

    def test_WHEN_auto_flow_set_THEN_pv_updates_and_states_are_set(self):
        card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        self.ca.set_pv_value("{}:PID:AUTO:SP".format(card_pv_prefix), "OFF")
        self.ca.set_pv_value("{}:FLOW:STAT:SP".format(card_pv_prefix), "Auto")
        self.ca.set_pv_value("{}:HEATER:MODE:SP".format(card_pv_prefix), "Manual")
        self.ca.set_pv_value("{}:FLOW:STAT:SP".format(pressure_card_pv_prefix), "Manual")

        self.ca.assert_setting_setpoint_sets_readback(
            "ON", set_point_pv="{}:SPC:SP".format(card_pv_prefix),
            readback_pv="{}:SPC".format(card_pv_prefix))
        self.ca.assert_that_pv_is("{}:PID:AUTO".format(card_pv_prefix), "ON")
        self.ca.assert_that_pv_is("{}:FLOW:STAT".format(card_pv_prefix), "Manual")
        self.ca.assert_that_pv_is("{}:HEATER:MODE".format(card_pv_prefix), "Auto")
        self.ca.assert_that_pv_is("{}:FLOW:STAT".format(pressure_card_pv_prefix), "Auto")
        self.ca.assert_that_pv_is("{}:SPC:SP".format(pressure_card_pv_prefix), "ON")

    def test_WHEN_auto_flow_set_off_THEN_pv_updates_and_states_are_not_set(self):
        card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        self.ca.set_pv_value("{}:PID:AUTO:SP".format(card_pv_prefix), "OFF")
        self.ca.set_pv_value("{}:FLOW:STAT:SP".format(card_pv_prefix), "Auto")
        self.ca.set_pv_value("{}:HEATER:MODE:SP".format(card_pv_prefix), "Manual")
        self.ca.set_pv_value("{}:FLOW:STAT:SP".format(pressure_card_pv_prefix), "Manual")

        self.ca.assert_setting_setpoint_sets_readback(
            "OFF", set_point_pv="{}:SPC:SP".format(card_pv_prefix),
            readback_pv="{}:SPC".format(card_pv_prefix), expected_alarm=self.ca.Alarms.MAJOR)
        self.ca.assert_that_pv_is("{}:PID:AUTO".format(card_pv_prefix), "OFF")
        self.ca.assert_that_pv_is("{}:FLOW:STAT".format(card_pv_prefix), "Auto")
        self.ca.assert_that_pv_is("{}:HEATER:MODE".format(card_pv_prefix), "Manual")
        self.ca.assert_that_pv_is("{}:FLOW:STAT".format(pressure_card_pv_prefix), "Manual")
        self.ca.assert_that_pv_is("{}:SPC:SP".format(pressure_card_pv_prefix), "OFF")

    def set_temp_reading_and_sp(self, reading, set_point, spc_state="On"):
        """
        Set the temperature in lewis and the set point on the first card
        :param reading: The reading lewis will return
        :param set_point: The set point to set on the device
        :param spc_state: State to set SPC to (defaults to On)
        """
        card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        self.ca.set_pv_value("{}:SPC:SP".format(card_pv_prefix), spc_state)
        self.ca.set_pv_value("{}:TEMP:SP".format(card_pv_prefix), set_point)
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", reading])

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_auto_flow_set_on_and_temp_lower_than_2_deadbands_THEN_pressure_set_to_minimum_pressure(self):
        set_point = 10
        reading = 10 - SPC_TEMP_DEADBAND * 2.1
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])
        self.set_temp_reading_and_sp(reading, set_point)

        self.ca.assert_that_pv_is("{}:PRESSURE:SP:RBV".format(pressure_card_pv_prefix), SPC_MIN_PRESSURE)

    @parameterized.expand([(10, ), (1, ), (300, ), (12, ), (20,)])
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_auto_flow_set_on_and_temp_low_but_within_1_to_2_deadbands_THEN_pressure_set_to_pressure_for_setpoint_temp_and_does_not_ramp(self, set_point):
        reading = set_point - SPC_TEMP_DEADBAND * 1.5
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])
        self.set_temp_reading_and_sp(reading, set_point)

        self.ca.assert_that_pv_is("{}:PRESSURE:SP:RBV".format(pressure_card_pv_prefix), pressure_for(set_point))
        sleep(1.5)
        self.ca.assert_that_pv_is("{}:PRESSURE:SP:RBV".format(pressure_card_pv_prefix), pressure_for(set_point))

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_auto_flow_set_on_and_temp_at_setpoint_THEN_pressure_set_to_pressure_for_setpoint_temp_and_does_ramp_down(self):
        set_point = 10
        reading = set_point
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])
        self.set_temp_reading_and_sp(reading, set_point)

        self.ca.assert_that_pv_is_number("{}:PRESSURE:SP".format(pressure_card_pv_prefix), pressure_for(set_point) + SPC_OFFSET, tolerance=SPC_OFFSET/4)  # should see number in ramp
        self.ca.assert_that_pv_is("{}:PRESSURE:SP".format(pressure_card_pv_prefix), pressure_for(set_point))  # final value

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_auto_flow_set_on_and_temp_above_setpoint_by_more_than_deadband_THEN_pressure_set_to_pressure_for_setpoint_temp_plus_gain_and_does_ramp(self):
        diff = SPC_TEMP_DEADBAND * 1.1
        set_point = 10
        reading = set_point + diff
        expected_pressure = pressure_for(set_point) + SPC_OFFSET + (abs(reading - set_point - SPC_TEMP_DEADBAND) * SPC_GAIN) ** 2
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])
        self.set_temp_reading_and_sp(reading, set_point)

        self.ca.assert_that_pv_is("{}:PRESSURE:SP".format(pressure_card_pv_prefix), expected_pressure)  # final value
        sleep(1.5)  # wait for possible ramp
        self.ca.assert_that_pv_is("{}:PRESSURE:SP".format(pressure_card_pv_prefix), expected_pressure)  # final value

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_auto_flow_set_on_and_pressure_would_be_high_THEN_pressure_set_to_maximum_pressure(self):
        diff = 1000
        set_point = 10
        reading = set_point + diff
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        self.set_temp_reading_and_sp(reading, set_point)

        self.ca.assert_that_pv_is("{}:PRESSURE:SP".format(pressure_card_pv_prefix), SPC_MAX_PRESSURE)  # final value

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_auto_flow_set_off_THEN_pressure_is_not_updated(self):
        diff = 1000
        set_point = 10
        reading = set_point + diff

        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])
        expected_value = -10
        self.ca.set_pv_value("{}:PRESSURE:SP".format(pressure_card_pv_prefix), expected_value)

        self.set_temp_reading_and_sp(reading, set_point, "OFF")

        self.ca.assert_that_pv_is("{}:PRESSURE:SP".format(pressure_card_pv_prefix), expected_value)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_auto_flow_on_but_error_in_temp_readback_THEN_pressure_is_not_updated(self):
        set_point = 10

        card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])
        expected_value = -10
        self.ca.set_pv_value("{}:PRESSURE:SP".format(pressure_card_pv_prefix), expected_value)

        with self._lewis.backdoor_simulate_disconnected_device():
            # we have a lot of db records scanning in the ioc, they will start to fail but it may take a while
            # (and this will be variable) before the record we choose gets processed and fails or hits
            # the stream device lock timeout instead.
            # So we need to wait for at least as long as stream device lock timeout to see an alarm raised`
            self.ca.assert_that_pv_alarm_is("{}:TEMP:SP:RBV".format(card_pv_prefix), self.ca.Alarms.INVALID, timeout=60)

            self.ca.set_pv_value("{}:SPC:SP".format(card_pv_prefix), "ON")
            self.ca.set_pv_value("{}:TEMP:SP".format(card_pv_prefix), set_point)

            self.ca.assert_that_pv_is("{}:PRESSURE:SP".format(pressure_card_pv_prefix), expected_value)
        
        self.ca.assert_that_pv_alarm_is("{}:TEMP:SP:RBV".format(card_pv_prefix), self.ca.Alarms.NONE, timeout=60)

    @parameterized.expand(parameterized_list(
        itertools.product(TEMP_CARDS + PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_voltage_updated_THEN_heater_voltage_percent_updated(self, _, card):
        original_voltage = 10
        new_voltage = 20
        voltage_limit = 50
        original_percent = 20
        new_percent = 40

        card_pv_prefix = get_card_pv_prefix(card)
        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage", original_voltage])
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage_limit", voltage_limit])

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), original_percent)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage", new_voltage])

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), new_percent)

    @parameterized.expand(parameterized_list(
        itertools.product(TEMP_CARDS + PRESSURE_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_voltage_limit_updated_then_voltage_percent_updated(self, _, card):
        voltage = 10
        original_limit = 50
        original_percent = 20
        new_limit = 20
        new_percent = 50

        card_pv_prefix = get_card_pv_prefix(card)
        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage", voltage])
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage_limit", original_limit])

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), original_percent)

        self.ca.set_pv_value("{}:HEATER:VOLT_LIMIT:SP".format(card_pv_prefix), new_limit)

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), new_percent)

    def test_WHEN_ioc_started_THEN_state_machine_initialized(self):
        self.ca.assert_that_pv_is("STATEMACHINE:STATE", "init")
        self.ca.assert_that_pv_alarm_is("STATEMACHINE:STATE", self.ca.Alarms.NONE)

    def test_WHEN_auto_pres_ctrl_disabled_THEN_statemachine_in_init(self):
        self.ca.set_pv_value("STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("STATEMACHINE:STATE", "init")
        self.ca.assert_that_pv_alarm_is("STATEMACHINE:STATUS", self.ca.Alarms.NONE)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_less_or_eq_tempsp_THEN_pressure_sp_set_to_pres_sp_minimum(self):
        self.ca.set_pv_value("STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 60)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:SP:MIN", 20)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 20, tolerance=0.01)
        
        self.ca.set_pv_value("STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 20, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_less_than_cutoff_THEN_pressure_set_to_constant(self):
        self.ca.set_pv_value("STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:SP:MIN", 1)
        self.ca.set_pv_value("VTI_SPC:TEMP:CUTOFF", 15)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:CONST", 5)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 5, tolerance=0.01)
        
        self.ca.set_pv_value("STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 5, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_less_than_cutoff_THEN_pressure_bounded_by_minimum(self):
        self.ca.set_pv_value("STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:SP:MIN", 12)
        self.ca.set_pv_value("VTI_SPC:TEMP:CUTOFF", 15)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:CONST", 7)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 12, tolerance=0.01)
        
        self.ca.set_pv_value("STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 12, tolerance=0.01)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_sm_on_WHEN_temp_sp_less_than_cutoff_THEN_pressure_bounded_by_maximum(self):
        self.ca.set_pv_value("STATEMACHINE:STATUS", "Off")
        self.ca.assert_that_pv_is("STATEMACHINE:STATE", "init")
        temp_card_pv_prefix = get_card_pv_prefix(TEMP_CARDS[0])
        pressure_card_pv_prefix = get_card_pv_prefix(PRESSURE_CARDS[0])

        # Set up the PVs for the low temp loop and start the statemachine
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [TEMP_CARDS[0], "temperature", 50])
        self.ca.set_pv_value(f"{temp_card_pv_prefix}:TEMP:SP", 10)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:SP:MIN", 5)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:SP:MAX", 17)
        self.ca.set_pv_value("VTI_SPC:TEMP:CUTOFF", 15)
        self.ca.set_pv_value("VTI_SPC:PRESSURE:CONST", 20)
        self.ca.set_pv_value(f"{pressure_card_pv_prefix}:PRESSURE:SP", 40)
        self.ca.assert_that_pv_is_not_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 17, tolerance=0.01)
        
        self.ca.set_pv_value("STATEMACHINE:STATUS", "On")

        self.ca.assert_that_pv_is_number(f"{pressure_card_pv_prefix}:PRESSURE:SP:RBV", 17, tolerance=0.01)
