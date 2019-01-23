from __future__ import division
import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc
from parameterized import parameterized


# Device prefix
DEVICE_PREFIX = "MOXA12XX_01"

LOW_ALARM_LIMIT = 2.0
HIGH_ALARM_LIMIT = 8.0

AI_REGISTER_OFFSET = 0

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MOXA12XX"),
        "emulator": "moxa12xx",
        "emulator_protocol": "MOXA_1240",
        "macros": {
            "IEOS": r"\\r\\n",
            "OEOS": r"\\r\\n",
            "MODELNO": "1240",
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

RANGE_STATUSES = {0: "NORMAL",
                  1: "BURNOUT",
                  2: "OVERRANGE",
                  3: "UNDERRANGE"}

TEST_VALUE = 5.0


class Moxa1240Tests(unittest.TestCase):
    """
    Tests for a moxa ioLogik e1240. (7x DC Voltage/Current measurements)
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("moxa12xx", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        # Sends a backdoor command to the device to set an analogue input (AI) value
        self._lewis.backdoor_run_function_on_device("set_ir", (0, [1]*8))
        for test_channel in CHANNELS:
            self.ca.assert_that_pv_is_number("CH{:01d}:AI:RAW".format(test_channel), 1, tolerance=0.1)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_an_AI_input_is_changed_THEN_that_channel_readback_updates(self, _, channel):
        self._lewis.backdoor_run_function_on_device("set_1240_voltage", (channel + AI_REGISTER_OFFSET, TEST_VALUE))

        self.ca.assert_that_pv_is_number("CH{:01d}:AI:RBV".format(channel), TEST_VALUE, tolerance=0.1)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_voltage_is_below_low_limit_THEN_PV_shows_major_alarm(self, _, channel):
        voltage_to_set = LOW_ALARM_LIMIT - 1.0

        self._lewis.backdoor_run_function_on_device("set_1240_voltage", (channel + AI_REGISTER_OFFSET, voltage_to_set))

        self.ca.assert_that_pv_alarm_is("CH{:01d}:AI:RBV".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_device_voltage_is_above_high_limit_THEN_PV_shows_major_alarm(self, _, channel):
        voltage_to_set = HIGH_ALARM_LIMIT + 1.0

        self._lewis.backdoor_run_function_on_device("set_1240_voltage", (channel + AI_REGISTER_OFFSET, voltage_to_set))

        self.ca.assert_that_pv_alarm_is("CH{:01d}:AI:RBV".format(channel), self.ca.Alarms.MAJOR)

    @parameterized.expand([
        ("CH{:01d}".format(channel), channel) for channel in CHANNELS
    ])
    def test_WHEN_a_channel_is_aliased_THEN_a_PV_with_that_alias_exists(self, _, channel):
        self.ca.assert_that_pv_exists(IOCS[0]["macros"]["CHAN{:01d}NAME".format(channel)])
