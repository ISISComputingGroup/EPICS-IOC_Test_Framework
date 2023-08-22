import unittest
from itertools import product

from common_tests.moxa12XX import Moxa12XXBase

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from parameterized import parameterized

# Device prefix
DEVICE_PREFIX = "MOXA12XX_01"
CHANNEL_FORMAT = "CHANNEL{:01d}"

NUMBER_OF_AI_CHANNELS = 4
NUMBER_OF_DI_CHANNELS = 8

SCALING_FACTOR = 10.0
LOW_ALARM_LIMIT = 2.0 * SCALING_FACTOR
HIGH_ALARM_LIMIT = 8.0 * SCALING_FACTOR

macros = {
    "IEOS": r"\\r\\n",
    "OEOS": r"\\r\\n",
    "MODELNO": "1242",
}

for channel in range(NUMBER_OF_AI_CHANNELS):
    macros["AICHAN{:1d}NAME".format(channel)] = CHANNEL_FORMAT.format(channel)
    macros["CHAN{:1d}LOWLIMIT".format(channel)] = LOW_ALARM_LIMIT
    macros["CHAN{:1d}HILIMIT".format(channel)] = HIGH_ALARM_LIMIT
    macros["CHAN{:1d}SCLEFACTR".format(channel)] = SCALING_FACTOR

for channel in range(NUMBER_OF_DI_CHANNELS):
    macros["DICHAN{:1d}NAME".format(channel)] = CHANNEL_FORMAT.format(channel)


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MOXA12XX"),
        "emulator": "moxa12xx",
        "lewis_protocol": "MOXA_1242",
        "macros": macros,
        "pv_for_existence": "CH1:AI:RBV",
    },
]

AI_REGISTER_OFFSET = 0x200
REGISTERS_PER_CHANNEL = 1

TEST_MODES = [TestModes.DEVSIM, ]

AICHANNELS = range(NUMBER_OF_AI_CHANNELS)
DICHANNELS = range(NUMBER_OF_DI_CHANNELS)

MIN_VOLT_MEAS = 0.0
MAX_VOLT_MEAS = 10.0

TEST_VALUES = [MIN_VOLT_MEAS,
               MAX_VOLT_MEAS,
               0.5*(MIN_VOLT_MEAS + MAX_VOLT_MEAS)]


class Moxa1242AITestsFromBase(Moxa12XXBase, unittest.TestCase):
    """
    Tests for the moxa 1242 (4x DC voltage/current measurements) inherited from base class.
    The unscaled readback test is not inherited.
    """

    def get_device_prefix(self):
        return DEVICE_PREFIX

    def get_PV_name(self):
        return "AI:SCALED"

    def get_number_of_channels(self):
        return NUMBER_OF_AI_CHANNELS

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
        for channel, test_value in product(AICHANNELS, TEST_VALUES):
            register_offset = channel * self.get_registers_per_channel()

            self._lewis.backdoor_run_function_on_device(self.get_setter_function_name(),
                                                        (self.get_starting_reg_addr() + register_offset, test_value))

            self.ca.assert_that_pv_is_number("CH{:01d}:AI:RBV".format(channel, PV=self.get_PV_name()),
                                             test_value, tolerance=0.1*abs(test_value))
                                             
    
class Moxa1242DITests(unittest.TestCase):   
    """
    Tests for the Moxa ioLogik e1242 Discrete Inputs. (8x Discrete inputs)
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("moxa12xx", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)

        # Sends a backdoor command to the device to set a discrete input (DI) value

        self._lewis.backdoor_run_function_on_device("set_di", (0, [False]*NUMBER_OF_DI_CHANNELS))

    def resetDICounter(self, channel):
        """
        Reset the counters for each DI (channel)

        Args:
            channel (int) : The DI (channel) counter to be reset

        We typically want to preserve our counter values for each channel even upon restart. For testing purposes
        this function will reset the counter values to 0. 
        """
        self.ca.set_pv_value("CH{:01d}:DI:CNT".format(channel), 0)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in DICHANNELS
    ])
    
    def test_WHEN_DI_input_is_switched_on_THEN_only_that_channel_readback_changes_to_state_just_set(self, _, channel):
        self._lewis.backdoor_run_function_on_device("set_di", (channel, (True,)))

        self.ca.assert_that_pv_is("CH{:d}:DI".format(channel), "High")

        # Test that all other channels are still off
        for test_channel in DICHANNELS:
            if test_channel == channel:
                continue

            self.ca.assert_that_pv_is("CH{:1d}:DI".format(test_channel), "Low")

    #@parameterized.expand([ This needs to be fixed in #7963
    #    ("CH{:01d}:DI:CNT".format(channel), channel) for channel in DICHANNELS
    #])
    #
    #def test_WHEN_di_input_is_triggered_a_number_of_times_THEN_di_counter_matches(self, channel_pv, channel):
    #    self.resetDICounter(channel)
    #    expected_count = 5
#
    #    for i in range(expected_count):
    #        # Toggle channel and ensure it's registered the trigger
    #        self._lewis.backdoor_run_function_on_device("set_di", (channel, (True,)))
    #        self.ca.assert_that_pv_is("CH{:d}:DI".format(channel), "High")
    #        self._lewis.backdoor_run_function_on_device("set_di", (channel, (False,)))
    #        self.ca.assert_that_pv_is("CH{:d}:DI".format(channel), "Low")
    #        self.ca.assert_that_pv_is(channel_pv, i+1, timeout=5)
#
    #    self.ca.assert_that_pv_is(channel_pv, expected_count)
