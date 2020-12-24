import time
import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "GAMRY_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("GAMRY"),
        "emulator": "gamry",
        "pv_for_existence": "CHARGE:STAT",
    },
]

TEST_MODES = [TestModes.DEVSIM]


class GamryTests(unittest.TestCase):
    """
    Tests for the Gamry.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("gamry", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_start_charging_WHEN_charge_completed_THEN_charging_finished_received(self):
        self.ca.assert_that_pv_is("CHARGE:STAT", "Idle")
        self.ca.set_pv_value("CHARGE:SP", 1)
        self.ca.assert_that_pv_is("CHARGE:STAT", "Charging", timeout=2)
        self.ca.assert_that_pv_is("CHARGE:STAT", "Idle", timeout=10)
