import unittest
from parameterized import parameterized
from itertools import product

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, parameterized_list

# Device prefix
DEVICE_PREFIX = "HLX503_01"

# Emulator name
emulator_name = "hlx503"

# ITC503 ISOBUS addresses and channels
# Must match those in emulator device
itc_names = ["SORB", "1KPOT", "HE3POT_LOWT", "HE3POT_HIGHT"]
itc_name_and_isobus = list(enumerate(itc_names))
isobus_addresses = {f"{name}_ISOBUS": isobus_address for isobus_address, name in enumerate(itc_names)}
channels = {f"{name}_CHANNEL": channel for channel, name in enumerate(itc_names)}
isobus_addresses_and_channels_zip = zip(isobus_addresses.values(), channels.values())
itc_zip = list(zip(itc_names, isobus_addresses.values(), channels.values()))

# Properties obtained from the get_status protocol and values to set them with
status_properties = [
    "status", "autoheat", "autoneedlevalve", "initneedlevalve", "remote",
    "locked", "sweeping", "ctrlchannel", "autopid", "tuning"
]
status_set_values = [
    8, True, True, True, True,
    True, 1, 5, True, True
]
status_expected_values = [
    8, "Auto", "Auto", "YES", "YES",
    "YES", "YES", 5, "ON", "YES"
]
status_properties_and_values = zip(status_properties, status_set_values, status_expected_values)
isobus_status_properties_and_values = product(itc_name_and_isobus, status_properties_and_values)
combo_one = [("autoheat", "autoneedlevalve", "initneedlevalve")]
combo_one_set_values = [
    (True, True, True),
    (True, False, True),
    (False, False, False),
    (True, True, False),
    (False, True, True),
]
combo_one_expected_values = [
    ("Auto", "Auto", "YES"),
    ("Auto", "Manual", "YES"),
    ("Manual", "Manual", "NO"),
    ("Auto", "Auto", "NO"),
    ("Manual", "Auto", "YES"),
]
combo_two = [("remote", "locked")]
combo_two_set_values = [
    (True, True),
    (False, False),
    (True, False),
    (False, True)
]
combo_two_expected_values = [
    ("YES", "YES"),
    ("NO", "NO"),
    ("YES", "NO"),
    ("NO", "YES")
]
combo_three = [("ctrlchannel", "autopid", "tuning")]
combo_three_set_values = [
    #
    (None, True, True),
    (None, False, True),
    (None, True, False),
    (None, False, False),
    #
    (None, None, None),
    (None, None, True),
    (None, None, False),
    (None, False, None),
    (None, True, None),
    #
    (5, True, True),
    (5, False, True),
    (5, True, False),
    (5, False, False),
    #
    (5, None, None),
    (5, None, True),
    (5, None, False),
    (5, False, None),
    (5, True, None),
]
combo_three_expected_values = [
    #
    (0, "ON", "YES"),
    (0, "OFF", "YES"),
    (0, "ON", "NO"),
    (0, "OFF", "NO"),
    #
    (0, "OFF", "NO"),
    (0, "OFF", "YES"),
    (0, "OFF", "NO"),
    (0, "OFF", "NO"),
    (0, "ON", "NO"),
    #
    (5, "ON", "YES"),
    (5, "OFF", "YES"),
    (5, "ON", "NO"),
    (5, "OFF", "NO"),
    #
    (5, "OFF", "NO"),
    (5, "OFF", "YES"),
    (5, "OFF", "NO"),
    (5, "OFF", "NO"),
    (5, "ON", "NO"),
]

status_combos = list(product(combo_one, zip(combo_one_set_values, combo_one_expected_values))) + \
                list(product(combo_two, zip(combo_two_set_values, combo_two_expected_values))) + \
                list(product(combo_three, zip(combo_three_set_values, combo_three_expected_values)))
itc_status_combos = list(product(itc_name_and_isobus, status_combos))

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
        for isobus_address in isobus_addresses.values():
            self._lewis.backdoor_run_function_on_device("reset_status", arguments=[isobus_address])

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

    @parameterized.expand(parameterized_list(isobus_status_properties_and_values))
    def test_WHEN_status_properties_set_via_backdoor_THEN_status_values_correct(self, _, isobus_and_itc, status_property_and_vals):
        status_property, status_set_val, status_expected_val = status_property_and_vals
        isobus_address, itc_name = isobus_and_itc
        self._lewis.backdoor_run_function_on_device(f"set_{status_property}", arguments=[isobus_address, status_set_val])
        self.ca.assert_that_pv_is(f"{itc_name}:{status_property.upper()}", status_expected_val)

    @parameterized.expand(parameterized_list(itc_status_combos))
    def test_WHEN_status_properties_set_in_combination_via_backdoor_THEN_status_values_correct(self, _, isobus_and_itc, status_property_and_vals):
        # Unpack status property and values
        properties = status_property_and_vals[0]
        set_vals = status_property_and_vals[1][0]
        expected_vals = status_property_and_vals[1][1]
        num_of_properties = len(properties)
        # Unpack isobus and itc address
        isobus_address, itc_name = isobus_and_itc
        for i in range(num_of_properties):
            self._lewis.backdoor_run_function_on_device(f"set_{properties[i]}", arguments=[isobus_address, set_vals[i]])
        for i in range(num_of_properties):
            self.ca.assert_that_pv_is(f"{itc_name}:{properties[i].upper()}", expected_vals[i])
