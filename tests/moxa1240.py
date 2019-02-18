from __future__ import division
import unittest

from common_tests.moxa12XX import Moxa12XXBase

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir


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

MIN_VOLT_MEAS = 0.0
MAX_VOLT_MEAS = 10.0

TEST_VALUES = [MIN_VOLT_MEAS,
               MAX_VOLT_MEAS,
               0.5*(MIN_VOLT_MEAS + MAX_VOLT_MEAS)]


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

