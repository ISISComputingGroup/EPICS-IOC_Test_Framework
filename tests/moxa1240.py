from __future__ import division
import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc
from parameterized import parameterized


# Device prefix
DEVICE_PREFIX = "MOXA12XX_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MOXA12XX"),
        "emulator": "moxa12xx",
        "emulator_protocol": "modbus",
        "macros": {
            "IEOS": r"\\r\\n",
            "OEOS": r"\\r\\n",
            "MODELNO": "1240"
        }
    },
]

TEST_MODES = [TestModes.DEVSIM, ]
CHANNELS = range(7)

TEST_VALUE = 50


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
        self._lewis.backdoor_run_function_on_device("set_ir", (channel, [TEST_VALUE, ]))

        self.ca.assert_that_pv_is_number("CH{:01d}:AI:RAW".format(channel), TEST_VALUE, tolerance=0.1)
