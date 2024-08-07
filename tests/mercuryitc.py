import itertools
import os
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import ManagerMode, get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

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
        return "{}".format(
            TEMP_CARDS.index(card) + 1
        )  # Only a numeric prefix for temperature cards
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

macros["CALIB_BASE_DIR"] = EPICS_TOP.replace("\\", "/")
macros["CALIB_DIR"] = os.path.join("support", "mercuryitc", "master", "settings").replace("\\", "/")


DEVICE_PREFIX = "MERCURY_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(
            EPICS_TOP, "ioc", "master", "MERCURY_ITC", "iocBoot", "iocMERCURY-IOC-01"
        ),
        "emulator": "mercuryitc",
        "macros": macros,
    },
    {
        # INSTETC is required to enable manager mode.
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    },
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
PRESSSURE_FOR = [
    (0, 35),
    (4, 35),
    (10, 25),
    (20, 14),
    (50, 10),
    (100, 8),
    (150, 8),
    (200, 8),
    (280, 8),
]


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

    @parameterized.expand(
        parameterized_list(
            itertools.product(PID_PARAMS, PID_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)
        )
    )
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_pid_params_set_via_backdoor_THEN_readback_updates(
        self, _, param, test_value, card
    ):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, param.lower(), test_value]
        )
        self.ca.assert_that_pv_is("{}:{}".format(card_pv_prefix, param), test_value)

    @parameterized.expand(
        parameterized_list(
            itertools.product(PID_PARAMS, PID_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)
        )
    )
    def test_WHEN_pid_params_set_THEN_readback_updates(self, _, param, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            readback_pv="{}:{}".format(card_pv_prefix, param),
            set_point_pv="{}:{}:SP".format(card_pv_prefix, param),
        )

    @parameterized.expand(
        parameterized_list(itertools.product(AUTOPID_MODES, TEMP_CARDS + PRESSURE_CARDS))
    )
    def test_WHEN_autopid_set_THEN_readback_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            readback_pv="{}:PID:AUTO".format(card_pv_prefix),
            set_point_pv="{}:PID:AUTO:SP".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, TEMP_CARDS))
    )
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_actual_temp_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "temperature", test_value]
        )
        self.ca.assert_that_pv_is("{}:TEMP".format(card_pv_prefix), test_value)

    @parameterized.expand(
        parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, PRESSURE_CARDS))
    )
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_actual_pressure_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "pressure", test_value]
        )
        self.ca.assert_that_pv_is("{}:PRESSURE".format(card_pv_prefix), test_value)

    @parameterized.expand(parameterized_list(itertools.product(RESISTANCE_TEST_VALUES, TEMP_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_resistance_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "resistance", test_value]
        )
        self.ca.assert_that_pv_is("{}:RESISTANCE".format(card_pv_prefix), test_value)

    @parameterized.expand(
        parameterized_list(itertools.product(RESISTANCE_TEST_VALUES, PRESSURE_CARDS))
    )
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_voltage_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "voltage", test_value]
        )
        self.ca.assert_that_pv_is("{}:VOLT".format(card_pv_prefix), test_value)

    @parameterized.expand(
        parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, TEMP_CARDS))
    )
    def test_WHEN_sp_temp_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            set_point_pv="{}:TEMP:SP".format(card_pv_prefix),
            readback_pv="{}:TEMP:SP:RBV".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(itertools.product(TEMPERATURE_TEST_VALUES, PRESSURE_CARDS))
    )
    def test_WHEN_sp_pressure_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            set_point_pv="{}:PRESSURE:SP".format(card_pv_prefix),
            readback_pv="{}:PRESSURE:SP:RBV".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(itertools.product(HEATER_MODES, TEMP_CARDS + PRESSURE_CARDS))
    )
    def test_WHEN_heater_mode_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode,
            set_point_pv="{}:HEATER:MODE:SP".format(card_pv_prefix),
            readback_pv="{}:HEATER:MODE".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(itertools.product(GAS_FLOW_MODES, TEMP_CARDS + PRESSURE_CARDS))
    )
    def test_WHEN_gas_flow_mode_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode,
            set_point_pv="{}:FLOW:STAT:SP".format(card_pv_prefix),
            readback_pv="{}:FLOW:STAT".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(itertools.product(GAS_FLOW_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS))
    )
    def test_WHEN_gas_flow_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode,
            set_point_pv="{}:FLOW:SP".format(card_pv_prefix),
            readback_pv="{}:FLOW".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(
            itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)
        )
    )
    def test_WHEN_heater_percent_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode,
            set_point_pv="{}:HEATER:SP".format(card_pv_prefix),
            readback_pv="{}:HEATER".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(
            itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)
        )
    )
    def test_WHEN_heater_voltage_limit_is_set_THEN_pv_updates(self, _, mode, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            mode,
            set_point_pv="{}:HEATER:VOLT_LIMIT:SP".format(card_pv_prefix),
            readback_pv="{}:HEATER:VOLT_LIMIT".format(card_pv_prefix),
        )

    @parameterized.expand(
        parameterized_list(
            itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)
        )
    )
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_power_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "power", test_value]
        )
        self.ca.assert_that_pv_is("{}:HEATER:POWER".format(card_pv_prefix), test_value)

    @parameterized.expand(
        parameterized_list(
            itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)
        )
    )
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_curr_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "current", test_value]
        )
        self.ca.assert_that_pv_is("{}:HEATER:CURR".format(card_pv_prefix), test_value)

    @parameterized.expand(
        parameterized_list(
            itertools.product(HEATER_PERCENT_TEST_VALUES, TEMP_CARDS + PRESSURE_CARDS)
        )
    )
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_heater_voltage_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        heater_chan_name = self.ca.get_pv_value("{}:HTRCHAN".format(card_pv_prefix))

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage", test_value]
        )
        self.ca.assert_that_pv_is("{}:HEATER:VOLT".format(card_pv_prefix), test_value)

    @parameterized.expand(
        parameterized_list(
            itertools.product(MOCK_NICKNAMES, TEMP_CARDS + PRESSURE_CARDS + LEVEL_CARDS)
        )
    )
    def test_WHEN_name_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self.ca.assert_setting_setpoint_sets_readback(
            test_value,
            readback_pv="{}:NAME".format(card_pv_prefix),
            set_point_pv="{}:NAME:SP".format(card_pv_prefix),
        )

    @parameterized.expand(parameterized_list(itertools.product(GAS_LEVEL_TEST_VALUES, LEVEL_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_helium_level_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "helium_level", test_value]
        )
        self.ca.assert_that_pv_is_number(
            "{}:HELIUM".format(card_pv_prefix), test_value, tolerance=0.01
        )

    @parameterized.expand(parameterized_list(itertools.product(GAS_LEVEL_TEST_VALUES, LEVEL_CARDS)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_nitrogen_level_is_set_via_backdoor_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [card, "nitrogen_level", test_value]
        )
        self.ca.assert_that_pv_is_number(
            "{}:NITROGEN".format(card_pv_prefix), test_value, tolerance=0.01
        )

    @parameterized.expand(
        parameterized_list(itertools.product(TEMP_CARDS + PRESSURE_CARDS, HEATER_CARDS))
    )
    def test_WHEN_heater_association_is_set_THEN_pv_updates(self, _, parent_card, associated_card):
        card_pv_prefix = get_card_pv_prefix(parent_card)

        with ManagerMode(ChannelAccess()):
            self.ca.assert_setting_setpoint_sets_readback(
                associated_card, "{}:HTRCHAN".format(card_pv_prefix)
            )

    @parameterized.expand(
        parameterized_list(itertools.product(TEMP_CARDS + PRESSURE_CARDS, AUX_CARDS))
    )
    def test_WHEN_aux_association_is_set_THEN_pv_updates(self, _, parent_card, associated_card):
        card_pv_prefix = get_card_pv_prefix(parent_card)
        with ManagerMode(ChannelAccess()):
            self.ca.assert_setting_setpoint_sets_readback(
                associated_card, "{}:AUXCHAN".format(card_pv_prefix)
            )

    @parameterized.expand(parameterized_list(itertools.product(HELIUM_READ_RATES, LEVEL_CARDS)))
    def test_WHEN_he_read_rate_is_set_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        self.ca.assert_setting_setpoint_sets_readback(
            test_value, "{}:HELIUM:READ_RATE".format(card_pv_prefix)
        )

    @parameterized.expand(
        parameterized_list(
            [
                ("CATALOG:PARSE.VALA", TEMP_CARDS),
                ("CATALOG:PARSE.VALB", PRESSURE_CARDS),
                ("CATALOG:PARSE.VALC", LEVEL_CARDS),
                ("CATALOG:PARSE.VALD", HEATER_CARDS),
                ("CATALOG:PARSE.VALE", AUX_CARDS),
            ]
        )
    )
    @skip_if_recsim("Complex logic not tested in recsim")
    def test_WHEN_getting_catalog_it_contains_all_cards(self, _, pv, cards):
        for card in cards:
            self.ca.assert_that_pv_value_causes_func_to_return_true(pv, lambda val: card in val)

    @parameterized.expand(
        parameterized_list(itertools.product(MOCK_CALIB_FILES, TEMP_CARDS + PRESSURE_CARDS))
    )
    def test_WHEN_setting_calibration_file_THEN_pv_updates(self, _, test_value, card):
        card_pv_prefix = get_card_pv_prefix(card)
        with ManagerMode(ChannelAccess()):
            self.ca.assert_setting_setpoint_sets_readback(
                test_value, "{}:CALFILE".format(card_pv_prefix)
            )

    @parameterized.expand(parameterized_list(["O", "R"]))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_resistance_suffix_is_changed_THEN_resistance_reads_correctly(
        self, _, resistance_suffix
    ):
        self._lewis.backdoor_set_on_device("resistance_suffix", resistance_suffix)
        resistance_value = 3
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property",
            [PRIMARY_TEMPERATURE_CHANNEL, "resistance", resistance_value],
        )
        self.ca.assert_that_pv_is(
            "{}:RESISTANCE".format(get_card_pv_prefix(PRIMARY_TEMPERATURE_CHANNEL)),
            resistance_value,
        )
        self.ca.assert_that_pv_alarm_is(
            "{}:RESISTANCE".format(get_card_pv_prefix(PRIMARY_TEMPERATURE_CHANNEL)),
            self.ca.Alarms.NONE,
        )

    @parameterized.expand(parameterized_list(itertools.product(TEMP_CARDS + PRESSURE_CARDS)))
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
            "backdoor_set_channel_property", [heater_chan_name, "voltage", original_voltage]
        )
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage_limit", voltage_limit]
        )

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), original_percent)

        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage", new_voltage]
        )

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), new_percent)

    @parameterized.expand(parameterized_list(itertools.product(TEMP_CARDS + PRESSURE_CARDS)))
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
            "backdoor_set_channel_property", [heater_chan_name, "voltage", voltage]
        )
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [heater_chan_name, "voltage_limit", original_limit]
        )

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), original_percent)

        self.ca.set_pv_value("{}:HEATER:VOLT_LIMIT:SP".format(card_pv_prefix), new_limit)

        self.ca.assert_that_pv_is("{}:HEATER:VOLT_PRCNT".format(card_pv_prefix), new_percent)
