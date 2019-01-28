from __future__ import division
import unittest

from common_tests.moxa12XX import Moxa12XXBase

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc
from parameterized import parameterized
from itertools import product


# Device prefix
DEVICE_PREFIX = "MOXA12XX_01"
CHANNEL_FORMAT = "CHANNEL{:01d}"

LOW_ALARM_LIMIT = 2.0
HIGH_ALARM_LIMIT = 8.0

NUMBER_OF_CHANNELS = 8

macros = {
    "IEOS": r"\\r\\n",
    "OEOS": r"\\r\\n",
    "MODELNO": "1240",
}
for channel in range(NUMBER_OF_CHANNELS):
    macros["CHAN{:1d}NAME".format(channel)] = CHANNEL_FORMAT.format(channel)
    macros["CHAN{:1d}LOWLIMIT".format(channel)] = LOW_ALARM_LIMIT
    macros["CHAN{:1d}HILIMIT".format(channel)] = HIGH_ALARM_LIMIT

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MOXA12XX"),
        "emulator": "moxa12xx",
        "emulator_protocol": "MOXA_1240",
        "macros": macros
    },
]

AI_REGISTER_OFFSET = 0
REGISTERS_PER_CHANNEL = 1

TEST_MODES = [TestModes.DEVSIM, ]
NUMBER_OF_CHANNELS = 8
CHANNELS = range(NUMBER_OF_CHANNELS)

RANGE_STATUSES = {0: "NORMAL",
                  1: "BURNOUT",
                  2: "OVERRANGE",
                  3: "UNDERRANGE"}

MIN_VOLT_MEAS = 0.0
MAX_VOLT_MEAS = 10.0

TEST_VALUES = [MIN_VOLT_MEAS,
               MAX_VOLT_MEAS,
               0.5*(MIN_VOLT_MEAS + MAX_VOLT_MEAS)]

FLUSH_VALUE = 0


class Moxa1240TestsFromBase(Moxa12XXBase, unittest.TestCase):
    """
    Tests for the moxa 40 (8x DV voltage/Current measurements) imported from base class
    """

    def get_device_prefix(self):
        return DEVICE_PREFIX

    def get_PV_name(self):
        return "AI:RBV"

    def get_number_of_channels(self):
        return NUMBER_OF_CHANNELS

    def get_setter_function_name(self):
        return "set_1240_voltage"

    def get_starting_reg_addr(self):
        return AI_REGISTER_OFFSET

    def get_test_values(self):
        return TEST_VALUES

    def get_raw_ir_setter(self):
        return "set_ir"

    def get_raw_ir_pv(self):
        return "get_ir"

    def get_alarm_limits(self):
        return [LOW_ALARM_LIMIT, HIGH_ALARM_LIMIT]

    def get_registers_per_channel(self):
        return REGISTERS_PER_CHANNEL

    def get_channel_format(self):
        return CHANNEL_FORMAT


class Moxa1240Tests(unittest.TestCase):
    """
    Tests for a moxa ioLogik e1240. (8x DC Voltage/Current measurements)
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("moxa12xx", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        # Write zero to each input register to clear the data in the emulator
        flush_value = 0
        self._lewis.backdoor_run_function_on_device("set_ir", (AI_REGISTER_OFFSET, [flush_value]*NUMBER_OF_CHANNELS))
        for test_channel in CHANNELS:
            self.ca.assert_that_pv_is_number("CH{:01d}:AI:RAW".format(test_channel), flush_value, tolerance=0.1)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel, test_value) for channel, test_value in product(CHANNELS, TEST_VALUES)
    ])
    def test_WHEN_an_AI_input_is_changed_THEN_that_channel_readback_updates(self, _, channel, test_value):
        self._lewis.backdoor_run_function_on_device("set_1240_voltage", (channel + AI_REGISTER_OFFSET, test_value))

        self.ca.assert_that_pv_is_number("CH{:01d}:AI:RBV".format(channel), test_value, tolerance=0.1)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_voltage_is_below_low_limit_THEN_PV_shows_major_alarm(self, _, channel):
        voltage_to_set = LOW_ALARM_LIMIT - 1.0

        self.ca.assert_that_pv_alarm_is("CH{:01d}:AI:RBV".format(channel), self.ca.Alarms.NONE)

        self._lewis.backdoor_run_function_on_device("set_1240_voltage", (channel + AI_REGISTER_OFFSET, voltage_to_set))

        self.ca.assert_that_pv_alarm_is("CH{:01d}:AI:RBV".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_voltage_is_above_high_limit_THEN_PV_shows_major_alarm(self, _, channel):
        valid_voltage = 0.5*(HIGH_ALARM_LIMIT + LOW_ALARM_LIMIT)

        self._lewis.backdoor_run_function_on_device("set_1240_voltage", (channel + AI_REGISTER_OFFSET, valid_voltage))

        self.ca.assert_that_pv_alarm_is("CH{:01d}:AI:RBV".format(channel), self.ca.Alarms.NONE)

        voltage_to_set = HIGH_ALARM_LIMIT + 1.0

        self.ca.assert_that_pv_alarm_is("CH{:01d}:AI:RBV".format(channel), self.ca.Alarms.NONE)

        self._lewis.backdoor_run_function_on_device("set_1240_voltage", (channel + AI_REGISTER_OFFSET, voltage_to_set))

        self.ca.assert_that_pv_alarm_is("CH{:01d}:AI:RBV".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_a_channel_is_aliased_THEN_a_PV_with_that_alias_exists(self, _, channel):
        self.ca.assert_that_pv_exists(IOCS[0]["macros"]["CHAN{:01d}NAME".format(channel)])
