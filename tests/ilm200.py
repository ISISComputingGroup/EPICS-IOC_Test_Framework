import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class Ilm200Tests(unittest.TestCase):
    """
    Tests for the Ilm200 IOC.
    """
    DEFAULT_SCAN_RATE = 1

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ilm200")
        self.ca = ChannelAccess(device_prefix="ILM200_01")
        self.ca.wait_for("VERSION", timeout=30)

    def test_GIVEN_ilm200_THEN_has_version(self):
        self.ca.assert_that_pv_is_not("VERSION", "")
        self.ca.assert_pv_alarm_is("VERSION", ChannelAccess.ALARM_NONE)

    def test_GIVEN_ilm_200_THEN_can_access_levels_for_three_channels(self):
        for i in range(1,4):
            self.ca.assert_pv_alarm_is("CH{}:LEVEL".format(i), ChannelAccess.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "No dynamic behaviour recsim")
    def test_GIVEN_ilm_200_THEN_channel_levels_change_over_time(self):
        for i in range(1,3):
            def not_equal(a, b):
                tolerance = 0.01
                return abs(a-b)/(a+b+tolerance) > tolerance
            self.ca.assert_pv_value_over_time("CH{}:LEVEL".format(i), 2*Ilm200Tests.DEFAULT_SCAN_RATE, not_equal)

