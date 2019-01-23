from __future__ import division
import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc
from parameterized import parameterized


# Device prefix
DEVICE_PREFIX = "MOXA12XX_01"

LOW_ALARM_LIMIT = 20.0
HIGH_ALARM_LIMIT = 80.0

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MOXA12XX"),
        "emulator": "moxa12xx",
        "emulator_protocol": "MOXA_1262",
        "macros": {
            "IEOS": r"\\r\\n",
            "OEOS": r"\\r\\n",
            "MODELNO": "1262",
            "CHAN0NAME": "CHANNEL0",
            "CHAN1NAME": "CHANNEL1",
            "CHAN2NAME": "CHANNEL2",
            "CHAN3NAME": "CHANNEL3",
            "CHAN4NAME": "CHANNEL4",
            "CHAN5NAME": "CHANNEL5",
            "CHAN6NAME": "CHANNEL6",
            "CHAN7NAME": "CHANNEL7",
            "CHAN0LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN1LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN2LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN3LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN4LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN5LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN6LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN7LOWLIMIT": LOW_ALARM_LIMIT,
            "CHAN0HILIMIT": HIGH_ALARM_LIMIT,
            "CHAN1HILIMIT": HIGH_ALARM_LIMIT,
            "CHAN2HILIMIT": HIGH_ALARM_LIMIT,
            "CHAN3HILIMIT": HIGH_ALARM_LIMIT,
            "CHAN4HILIMIT": HIGH_ALARM_LIMIT,
            "CHAN5HILIMIT": HIGH_ALARM_LIMIT,
            "CHAN6HILIMIT": HIGH_ALARM_LIMIT,
            "CHAN7HILIMIT": HIGH_ALARM_LIMIT,
        }
    },
]

TEST_MODES = [TestModes.DEVSIM, ]
CHANNELS = range(7)

AI_REGISTER_OFFSET = 0x810

RANGE_STATUSES = {0: "NORMAL",
                  1: "BURNOUT",
                  2: "OVERRANGE",
                  3: "UNDERRANGE"}

TEST_VALUE = 50.0


class Moxa1262Tests(unittest.TestCase):
    """
    Tests for a moxa ioLogik e1262. (7x Thermocopule measurements)
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("moxa12xx", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        # Sends a backdoor command to the device to set an analogue input (AI) value
        self._lewis.backdoor_run_function_on_device("set_ir", (AI_REGISTER_OFFSET, [0]*16))

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_an_AI_input_is_changed_THEN_that_channel_readback_updates(self, _, channel):
        channel_address = AI_REGISTER_OFFSET + 2 * channel

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, TEST_VALUE))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP:RBV".format(channel), TEST_VALUE, tolerance=0.1)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_temperature_is_below_low_limit_THEN_PV_shows_major_alarm(self, _, channel):
        channel_address = AI_REGISTER_OFFSET + 2 * channel

        temperature_to_set = LOW_ALARM_LIMIT - 10.0

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, temperature_to_set))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP:RBV".format(channel), temperature_to_set)

        self.ca.assert_that_pv_alarm_is("CH{:01d}:TEMP:RBV".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_temperature_is_above_high_limit_THEN_PV_shows_major_alarm(self, _, channel):
        channel_address = AI_REGISTER_OFFSET + 2 * channel

        temperature_to_set = HIGH_ALARM_LIMIT + 10.0

        self._lewis.backdoor_run_function_on_device("set_1262_temperature", (channel_address, temperature_to_set))

        self.ca.assert_that_pv_is_number("CH{:01d}:TEMP:RBV".format(channel), temperature_to_set)

        self.ca.assert_that_pv_alarm_is("CH{:01d}:TEMP:RBV".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_a_channel_is_aliased_THEN_a_PV_with_that_alias_exists(self, _, channel):
        self.ca.assert_that_pv_exists(IOCS[0]["macros"]["CHAN{:01d}NAME".format(channel)])
