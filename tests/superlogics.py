import unittest

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc

# Internal Address of device (must be 2 characters)
ADDRESS = "02"

# MACROS to use for the IOC
MACROS = {"ADDR": ADDRESS}

# Prefix for addressing PVs on this device
PREFIX = "SPRLG_01"


class SuperlogicsTests(unittest.TestCase):
    """
    Tests for the Superlogics device
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("superlogics")

        self.ca = ChannelAccess()
        self.ca.wait_for("{0}:{1}:1:VALUE".format(PREFIX, ADDRESS))

    def _set_channel_values(self, values):
        self._lewis.backdoor_set_on_device("values", values)

    def test_GIVEN_channel_one_value_set_WHEN_read_THEN_value_is_as_expected(self):
        channel = 1
        expected_value = 1.3
        self._set_channel_values([expected_value])

        pv_name = "{0}:{1}:{2}:VALUE".format(PREFIX, ADDRESS, channel)
        self.ca.assert_that_pv_is(pv_name, expected_value)

    def test_GIVEN_channel_two_value_set_WHEN_read_THEN_value_is_as_expected(self):
        channel = 2
        expected_value = 2.0
        self._set_channel_values([0., expected_value])

        pv_name = "{0}:{1}:{2}:VALUE".format(PREFIX, ADDRESS, channel)
        self.ca.assert_that_pv_is(pv_name, expected_value)

    def test_GIVEN_all_channels_value_set_WHEN_read_THEN_value_is_as_expected(self):
        expected_values = [1., 2., 3., 4., 5., 6., 7., 8.]
        self._set_channel_values(expected_values)

        for channel, expected_value in enumerate(expected_values):
            pv_name = "{0}:{1}:{2}:VALUE".format(PREFIX, ADDRESS, channel+1)
            self.ca.assert_that_pv_is(pv_name, expected_value)

