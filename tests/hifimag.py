import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes

# Device prefix
DEVICE_PREFIX = "HIFIMAG_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HIFIMAG"),
    },
]


TEST_MODES = [TestModes.RECSIM]


class HifimagTests(unittest.TestCase):
    """
    Tests for the HIFIMAG.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(20, DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")
