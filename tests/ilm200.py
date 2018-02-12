import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class Ilm200Tests(unittest.TestCase):
    """
    Tests for the Ilm200 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ilm200")
        self.ca = ChannelAccess(device_prefix="ILM200_01")
        self.ca.wait_for("VERSION", timeout=30)

    def test_that_fails(self):
        self.fail("You haven't implemented any tests!")
