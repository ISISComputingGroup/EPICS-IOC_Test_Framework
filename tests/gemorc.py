import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class GemorcTests(unittest.TestCase):
    """
    Tests for the Gemorc IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Gemorc")
        self.ca = ChannelAccess(device_prefix="GEMORC_01")

    def test_that_fails(self):
        self.fail("You haven't implemented any tests!")
