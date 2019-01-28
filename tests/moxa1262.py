from __future__ import division
import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc
from parameterized import parameterized
from itertools import product

from common_tests.moxa12XX import Moxa12XXBase

# Device prefix
CHANNEL_FORMAT = "CHANNEL{:1d}"
DEVICE_PREFIX = "MOXA12XX_01"

LOW_ALARM_LIMIT = 20.0
HIGH_ALARM_LIMIT = 80.0

NUMBER_OF_CHANNELS = 8

macros = {
    "IEOS": r"\\r\\n",
    "OEOS": r"\\r\\n",
    "MODELNO": "1262",
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
        "emulator_protocol": "MOXA_1262",
        "macros": macros
    },
]

TEST_MODES = [TestModes.DEVSIM, ]

NUMBER_OF_CHANNELS = 8
REGISTERS_PER_CHANNEL = 2

CHANNELS = range(NUMBER_OF_CHANNELS)

AI_REGISTER_OFFSET = 0x810

RANGE_STATUSES = {0: "NORMAL",
                  1: "BURNOUT",
                  2: "OVERRANGE",
                  3: "UNDERRANGE"}

LARGEST_OBSERVABLE_VALUE = 3.4e38
SMALLEST_TYPE_K_MEAS = -180.0
LARGEST_TYPE_K_MEAS = 1300.0

TEST_VALUES = [LARGEST_OBSERVABLE_VALUE, SMALLEST_TYPE_K_MEAS, LARGEST_TYPE_K_MEAS]


class Moxa1262TestsFromBase(Moxa12XXBase, unittest.TestCase):
    """
    Tests for the moxa 1262 (8x Thermocouple measurements) imported from base class
    """

    def get_device_prefix(self):
        return DEVICE_PREFIX

    def get_PV_name(self):
        return "TEMP"

    def get_number_of_channels(self):
        return NUMBER_OF_CHANNELS

    def get_setter_function_name(self):
        return "set_1262_temperature"

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


class Moxa1262Tests(unittest.TestCase):
    """
    Tests for a moxa ioLogik e1262. (8x Thermocopule measurements)
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("moxa12xx", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        # Sends a backdoor command to the device to reset all input registers (IRs) to 0
        reset_value = 0
        self._lewis.backdoor_run_function_on_device("set_ir",
                                                    (AI_REGISTER_OFFSET,
                                                     [reset_value]*NUMBER_OF_CHANNELS*REGISTERS_PER_CHANNEL))

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel, test_value) for channel, test_value in product(CHANNELS, TEST_VALUES)
    ])
    def test_WHEN_an_AI_input_is_changed_THEN_that_channel_readback_updates(self, _, channel, test_value):
        channel_address = AI_REGISTER_OFFSET + REGISTERS_PER_CHANNEL * channel

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, test_value))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP".format(channel), test_value, tolerance=max(0.1, 0.1*test_value))

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_temperature_is_below_low_limit_THEN_PV_shows_major_alarm(self, _, channel):
        channel_address = AI_REGISTER_OFFSET + REGISTERS_PER_CHANNEL * channel

        valid_temperature = 0.5*(HIGH_ALARM_LIMIT + LOW_ALARM_LIMIT)

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, valid_temperature))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP".format(channel), valid_temperature, tolerance=0.1*valid_temperature)

        self.ca.assert_that_pv_alarm_is("CH{:01d}:TEMP".format(channel), self.ca.Alarms.NONE)

        temperature_to_set = LOW_ALARM_LIMIT - 10.0

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, temperature_to_set))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP".format(channel), temperature_to_set, tolerance=0.01*temperature_to_set)

        self.ca.assert_that_pv_alarm_is("CH{:01d}:TEMP".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_temperature_is_above_high_limit_THEN_PV_shows_major_alarm(self, _, channel):
        channel_address = AI_REGISTER_OFFSET + REGISTERS_PER_CHANNEL * channel

        valid_temperature = 0.5*(HIGH_ALARM_LIMIT + LOW_ALARM_LIMIT)

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, valid_temperature))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP".format(channel), valid_temperature, tolerance=0.1*valid_temperature)
        self.ca.assert_that_pv_alarm_is("CH{:01d}:TEMP".format(channel), self.ca.Alarms.NONE)

        temperature_to_set = HIGH_ALARM_LIMIT + 10.0

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, temperature_to_set))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP".format(channel), temperature_to_set, tolerance=0.01*temperature_to_set)

        self.ca.assert_that_pv_alarm_is("CH{:01d}:TEMP".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_a_channel_is_aliased_THEN_a_PV_with_that_alias_exists(self, _, channel):
        self.ca.assert_that_pv_exists(CHANNEL_FORMAT.format(channel))
