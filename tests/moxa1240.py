import unittest
from itertools import product

from common_tests.moxa12XX import Moxa12XXBase

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

# Device prefix
DEVICE_PREFIX = "MOXA12XX_01"
CHANNEL_FORMAT = "CHANNEL{:01d}"


NUMBER_OF_CHANNELS = 8

SCALING_FACTOR = 10.0
LOW_ALARM_LIMIT = 2.0 * SCALING_FACTOR
HIGH_ALARM_LIMIT = 8.0 * SCALING_FACTOR

macros = {
    "IEOS": r"\\r\\n",
    "OEOS": r"\\r\\n",
    "MODELNO": "1240",
}
for channel in range(NUMBER_OF_CHANNELS):
    macros["CHAN{:1d}NAME".format(channel)] = CHANNEL_FORMAT.format(channel)
    macros["CHAN{:1d}LOWLIMIT".format(channel)] = LOW_ALARM_LIMIT
    macros["CHAN{:1d}HILIMIT".format(channel)] = HIGH_ALARM_LIMIT
    macros["CHAN{:1d}SCLEFACTR".format(channel)] = SCALING_FACTOR

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MOXA12XX"),
        "emulator": "moxa12xx",
        "lewis_protocol": "MOXA_1240",
        "macros": macros,
        "pv_for_existence": "CH1:AI:RBV",
    },
]

AI_REGISTER_OFFSET = 0
REGISTERS_PER_CHANNEL = 1

TEST_MODES = [
    TestModes.DEVSIM,
]
NUMBER_OF_CHANNELS = 8
CHANNELS = range(NUMBER_OF_CHANNELS)

MIN_VOLT_MEAS = 0.0
MAX_VOLT_MEAS = 10.0

TEST_VALUES = [MIN_VOLT_MEAS, MAX_VOLT_MEAS, 0.5 * (MIN_VOLT_MEAS + MAX_VOLT_MEAS)]


class Moxa1240TestsFromBase(Moxa12XXBase, unittest.TestCase):
    """
    Tests for the moxa 1240 (8x DC voltage/current measurements) inherited from base class.
    The unscaled readback test is not inherited.
    """

    def get_device_prefix(self):
        return DEVICE_PREFIX

    def get_PV_name(self):
        return "AI:SCALED"

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

    def get_scaling_factor(self):
        return SCALING_FACTOR

    def test_WHEN_an_AI_input_is_changed_THEN_that_unscaled_channel_readback_updates(self):
        for channel, test_value in product(CHANNELS, TEST_VALUES):
            register_offset = channel * self.get_registers_per_channel()

            self._lewis.backdoor_run_function_on_device(
                self.get_setter_function_name(),
                (self.get_starting_reg_addr() + register_offset, test_value),
            )

            self.ca.assert_that_pv_is_number(
                "CH{:01d}:AI:RBV".format(channel, PV=self.get_PV_name()),
                test_value,
                tolerance=0.1 * abs(test_value),
            )
