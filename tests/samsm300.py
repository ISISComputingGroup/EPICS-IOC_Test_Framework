import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class Samsm300Tests(unittest.TestCase):
    """
    Tests for the Samsm300 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Samsm300")
        self.ca = ChannelAccess(device_prefix="SAMSM300_01")

    def test_that_fails(self):
        self.fail("You haven't implemented any tests!")
