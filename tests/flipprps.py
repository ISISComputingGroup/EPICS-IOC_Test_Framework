import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "FLIPPRPS_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FLIPPRPS"),
        "macros": {},
        "emulator": "flipprps",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class FlipprpsTests(unittest.TestCase):
    """
    Tests for the Flipprps IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("flipprps", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    @skip_if_recsim("Lewis backdoor commands not available in RecSim")
    def test_SET_polarity(self):
        self.ca.set_pv_value("POLARITY", "Down")
        polarity = self._lewis.backdoor_get_from_device("polarity")
        self.assertEqual(polarity, "0")
        self.ca.set_pv_value("POLARITY", "Up")
        polarity = self._lewis.backdoor_get_from_device("polarity")
        self.assertEqual(polarity, "1")