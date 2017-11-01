import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class Skf_mb350_chopperTests(unittest.TestCase):
    """
    Tests for the SKF MB350 Chopper IOC.
    """

    def setUp(self):
        pass

    def test_fail(self):
        self.assertFalse(True)

    def test_pass(self):
        self.assertFalse(False)

