import unittest

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc

# Internal Address of device (must be 2 characters)
ADDRESS = "01"

# MACROS to use for the IOC
MACROS = {"ADDR": ADDRESS}


class SuperlogicsTests(unittest.TestCase):
    """
    Tests for the Superlogics device
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("superlogics")

        self.ca = ChannelAccess()
        self.ca.wait_for("SPRLG_01:01:1:VALUE")

    def _set_channel_value(self, channel, value):
        pv_name = "SPRLG_01:SIM:{0}:{1}:VALUE".format(ADDRESS, channel)
        self._lewis.backdoor_set_on_device("value{0}".format(channel), value)
        self._ioc.set_simulated_value(pv_name, value)

    def test_GIVEN_modules_set_WHEN_read_THEN_modules_are_as_expected(self):
        channel = 1
        expected_value = 1.3
        self._set_channel_value(channel, expected_value)

        pv_name = "SPRLG_01:01:1:VALUE"
        self.ca.assert_that_pv_is(pv_name, expected_value)
