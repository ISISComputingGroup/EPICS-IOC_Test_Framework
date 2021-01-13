import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes

DEVICE_PREFIX = "FMR_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FMR"),
        "macros": {"LVDCOM_OPTIONS": 1},
    },
]


TEST_MODES = [TestModes.RECSIM]


class FmrTests(unittest.TestCase):
    """
    Tests for the fmr IOC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_is_started_THEN_PV_exists(self):
        self.ca.assert_that_pv_exists("FMR:ACTIVITY", timeout=30)
