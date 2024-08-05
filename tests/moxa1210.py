import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "MOXA12XX_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MOXA12XX"),
        "emulator": "moxa12xx",
        "lewis_protocol": "MOXA_1210",
        "macros": {"IEOS": r"\\r\\n", "OEOS": r"\\r\\n", "MODELNO": "1210"},
        "pv_for_existence": "CH1:DI",
    },
]

TEST_MODES = [
    TestModes.DEVSIM,
]

NUMBER_OF_CHANNELS = 16

CHANNELS = range(NUMBER_OF_CHANNELS)


class Moxa1210Tests(unittest.TestCase):
    """
    Tests for the Moxa ioLogik e1210. (16x Discrete inputs)
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("moxa12xx", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)

        # Sends a backdoor command to the device to set a discrete input (DI) value

        self._lewis.backdoor_run_function_on_device("set_di", (0, [False] * 16))

    def resetDICounter(self, channel):
        """
        Reset the counters for each DI (channel)

        Args:
            channel (int) : The DI (channel) counter to be reset

        We typically want to preserve our counter values for each channel even upon restart. For testing purposes
        this function will reset the counter values to 0.
        """
        self.ca.set_pv_value("CH{:01d}:DI:CNT".format(channel), 0)

    @parameterized.expand([("CH{:01d}".format(channel), channel) for channel in CHANNELS])
    def test_WHEN_DI_input_is_switched_on_THEN_only_that_channel_readback_changes_to_state_just_set(
        self, _, channel
    ):
        self._lewis.backdoor_run_function_on_device("set_di", (channel, (True,)))

        self.ca.assert_that_pv_is("CH{:d}:DI".format(channel), "High")

        # Test that all other channels are still off
        for test_channel in CHANNELS:
            if test_channel == channel:
                continue

            self.ca.assert_that_pv_is("CH{:1d}:DI".format(test_channel), "Low")

    @parameterized.expand([("CH{:01d}:DI:CNT".format(channel), channel) for channel in CHANNELS])
    def test_WHEN_di_input_is_triggered_a_number_of_times_THEN_di_counter_matches(
        self, channel_pv, channel
    ):
        self.resetDICounter(channel)
        expected_count = 5

        for i in range(expected_count):
            # Toggle channel and ensure it's registered the trigger
            self._lewis.backdoor_run_function_on_device("set_di", (channel, (True,)))
            self.ca.assert_that_pv_is("CH{:d}:DI".format(channel), "High")
            self._lewis.backdoor_run_function_on_device("set_di", (channel, (False,)))
            self.ca.assert_that_pv_is("CH{:d}:DI".format(channel), "Low")
            self.ca.assert_that_pv_is(channel_pv, i + 1, timeout=5)

        self.ca.assert_that_pv_is(channel_pv, expected_count)
