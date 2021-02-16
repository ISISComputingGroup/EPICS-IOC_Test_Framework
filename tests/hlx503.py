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

# ITC503 ISOBUS addresses
isobus_addresses = {
    "SORB_ISOBUS": 1,
    "1KPOT_ISOBUS": 2,
    "HE3POT_LOWT_ISOBUS": 3,
    "HE3POT_HIGHT_ISOBUS": 4
}

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulator": emulator_name,
        "macros": isobus_addresses
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ISOBUS503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(emulator_name, DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_started_THEN_ioc_connected(self):
        self.ca.get_pv_value("DISABLE")

    @parameterized.expand(parameterized_list(isobus_addresses.items()))
    def test_WHEN_ioc_set_up_with_ISOBUS_numbers_THEN_ISOBUS_numbers_are_correct(self, _, macro_pv_name, isobus_addresses):
        self.ca.assert_that_pv_is(macro_pv_name, isobus_addresses)
