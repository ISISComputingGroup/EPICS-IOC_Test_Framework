import unittest
from parameterized import parameterized

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, parameterized_list

# Device prefix
DEVICE_PREFIX = "HLX503_01"

# Emulator name
emulator_name = "hlx503"

# ITC503 numbers and channels
itc_numbers = {
    "SORB_ITC": 1,
    "1KPOT_ITC": 2,
    "HE3POT_LOWT_ITC": 3,
    "HE3POT_HIGHT_ITC": 4
}
channel_numbers = {
    "SORB_CH": 1,
    "1KPOT_CH": 2,
    "HE3POT_LOWT_CH": 3,
    "HE3POT_HIGHT_CH": 4
}

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulator": emulator_name,
        "macros": {**itc_numbers, **channel_numbers}
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ITC503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(emulator_name, DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_started_THEN_ioc_connected(self):
        self.ca.get_pv_value("DISABLE")

    @parameterized.expand(parameterized_list(itc_numbers.items()))
    def test_WHEN_ioc_set_up_with_itc_numbers_THEN_itc_numbers_are_correct(self, _, macro_pv_name, itc_address):
        self.ca.assert_that_pv_is(macro_pv_name, itc_address)

    @parameterized.expand(parameterized_list(channel_numbers.items()))
    def test_WHEN_ioc_set_up_with_channels_THEN_channels_are_correct(self, _, macro_pv_name, itc_address):
        self.ca.assert_that_pv_is(macro_pv_name, itc_address)

