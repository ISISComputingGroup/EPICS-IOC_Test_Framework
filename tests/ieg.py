import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

from time import sleep


class IegTests(unittest.TestCase):
    """
    Tests for the IEG IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ieg")

        self.ca = ChannelAccess(20)
        self.ca.wait_for("IEG_01:DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("IEG_01:DISABLE", "COMMS ENABLED")

    def test_set_mode(self):
        for i in range(1, 5):
            self.ca.set_pv_value("IEG_01:MODE:SP", i)
            sleep(5)