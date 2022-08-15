import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, unstable_test

# Prefix for addressing PVs on this device
PREFIX = "SPRLG_01"


IOCS = [
    {
        "name": PREFIX,
        "directory": get_default_ioc_dir("SPRLG"),
        "macros": {
            "HAS_CHAN1": "Y",
            "HAS_CHAN2": "Y",
        },
        "emulator": "superlogics",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class SuperlogicsTests(unittest.TestCase):
    """
    Tests for the Superlogics device
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("superlogics", PREFIX)

        self.ca = ChannelAccess(device_prefix=PREFIX)
        self.ca.assert_that_pv_exists("{}:1:VALUE".format("01"))

    def _set_channel_values(self, values, address):
        """
        Set the values for each of the channels on a given address
        :param values: the new values for each channel
        :param address: the address to set the channel values for
        """
        self._lewis.backdoor_set_on_device("values_{0}".format(int(address)), values)

        for i, value in enumerate(values):
            channel = i+1
            pv_name = "SIM:{}:{}:VALUE".format(address, channel)
            self._ioc.set_simulated_value(pv_name, value)

    def _set_firmware_version(self, value, address):
        """
        Set the firmware version
        :param value: the value to set the firmware version to
        :param address: the address to set the firmware version on
        """
        self._lewis.backdoor_set_on_device("version_{0}".format(int(address)), value)
        pv_name = "SIM:{}:VERSION".format(address)
        self._ioc.set_simulated_value(pv_name, value)


    def test_GIVEN_address_01_one_value_set_WHEN_read_THEN_value_is_as_expected(self):
        address = "01"
        channel = 1
        expected_value = 1.3
        self._set_channel_values([expected_value], address)

        pv_name = "{}:{}:VALUE".format(address, channel)
        self.ca.assert_that_pv_is(pv_name, expected_value)
        self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_address_01_all_channels_value_set_WHEN_read_THEN_error_state(self):
        address = "01"
        expected_values = [1., 2., 3., 4., 5., 6., 7., 8.]
        self._set_channel_values(expected_values, address)

        pv_name = "{}:{}:VALUE".format(address, 1)
        self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.INVALID)

    def test_GIVEN_address_01_version_set_WHEN_read_THEN_value_is_as_expected(self):
        address = "01"
        expected_version = "B1.0"
        self._set_firmware_version(expected_version, address)
        pv_name = "{}:VERSION".format(address)

        self.ca.assert_that_pv_is(pv_name, expected_version)
        self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_address_02_one_value_set_WHEN_read_THEN_error_state(self):
        address = "02"
        channel = 1
        expected_value = 1.3
        self._set_channel_values([expected_value], address)

        pv_name = "{}:{}:VALUE".format(address, channel)
        self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.INVALID)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_address_02_two_values_set_WHEN_read_THEN_error_state(self):
        address = "02"
        channel = 2
        expected_value = 2.0
        self._set_channel_values([0., expected_value], address)

        pv_name = "{}:{}:VALUE".format(address, channel)
        self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.INVALID)

    def test_GIVEN_address_02_all_channels_value_set_WHEN_read_THEN_values_are_as_expected(self):
        address = "02"
        expected_values = [1., 2., 3., 4., 5., 6., 7., 8.]
        self._set_channel_values(expected_values, address)

        for channel, expected_value in enumerate(expected_values):
            pv_name = "{}:{}:VALUE".format(address, channel+1)
            self.ca.assert_that_pv_is(pv_name, expected_value)
            self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.NONE)

    def test_GIVEN_address_02_version_set_WHEN_read_THEN_value_is_as_expected(self):
        address = "02"
        expected_version = "B1.0"
        self._set_firmware_version(expected_version, address)
        pv_name = "{}:VERSION".format(address)

        self.ca.assert_that_pv_is(pv_name, expected_version)
        self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.NONE)

    @unstable_test()
    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_address_02_disconnected_WHEN_read_values_THEN_error_state(self):
        address = "02"
        expected_values = [1., 2., 3., 4., 5., 6., 7., 8.]
        self._set_channel_values(expected_values, address)
        
        with self._lewis.backdoor_simulate_disconnected_device():
            for channel, expected_value in enumerate(expected_values):
                pv_name = "{}:{}:VALUE".format(address, channel+1)
                self.ca.assert_that_pv_alarm_is(pv_name, self.ca.Alarms.INVALID)
