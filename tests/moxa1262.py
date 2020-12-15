import unittest

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

from common_tests.moxa12XX import Moxa12XXBase

# Device prefix
CHANNEL_FORMAT = "CHANNEL{:1d}"
DEVICE_PREFIX = "MOXA12XX_01"

LOW_ALARM_LIMIT = 20.0
HIGH_ALARM_LIMIT = 80.0

NUMBER_OF_CHANNELS = 8

SCALING_FACTOR = 1.0

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
        "lewis_protocol": "MOXA_1262",
        "macros": macros,
        "pv_for_existence": "CH1:TEMP",
    },
]

TEST_MODES = [TestModes.DEVSIM, ]

NUMBER_OF_CHANNELS = 8
REGISTERS_PER_CHANNEL = 2

AI_REGISTER_OFFSET = 0x810

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

    def get_scaling_factor(self):
        return SCALING_FACTOR
