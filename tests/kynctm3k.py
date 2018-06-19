import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KYNCTM3K_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KYNCTM3K"),
        "macros": {},
        "emulator": "Kynctm3K",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Kynctm3KTests(unittest.TestCase):
    """
    Tests for the Kynctm3K IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Kynctm3K", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_that_fails(self):
        self.fail("You haven't implemented any tests!")
