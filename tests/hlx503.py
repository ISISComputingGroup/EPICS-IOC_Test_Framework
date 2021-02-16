import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "HLX503_01"

# Emulator name
emulator_name = "hlx503"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulator": emulator_name,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ITC503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(emulator_name, DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

