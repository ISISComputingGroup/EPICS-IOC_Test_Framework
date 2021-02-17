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

# ITC503 ISOBUS addresses and channels
itc_names = ["SORB", "1KPOT", "HE3POT_LOWT", "HE3POT_HIGHT"]
isobus_addresses = {f"{name}_ISOBUS": i for i, name in enumerate(itc_names)}
channels = {f"{name}_CHANNEL": i for i, name in enumerate(itc_names)}
isobus_addresses_and_channels_zip = zip(isobus_addresses.values(), channels.values())
itc_zip = zip(itc_names, isobus_addresses.values(), channels.values())

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulator": emulator_name,
        "macros": {**isobus_addresses, **channels}
    },
]


TEST_MODES = [TestModes.DEVSIM]


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
    def test_WHEN_ioc_set_up_with_ISOBUS_numbers_THEN_ISOBUS_numbers_are_correct(self, _, macro_pv_name, isobus_address):
        self.ca.assert_that_pv_is(macro_pv_name, isobus_address)

    @parameterized.expand(parameterized_list(itc_zip))
    def test_WHEN_set_temp_via_backdoor_THEN_get_temp_value_correct(self, _, itc_name, isobus_address, channel):
        temp = 20.0
        self._lewis.backdoor_run_function_on_device("set_temp", arguments=(isobus_address, channel, temp))
        self.ca.assert_that_pv_is(f"{itc_name}:TEMP", temp)
