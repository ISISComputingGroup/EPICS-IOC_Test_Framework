import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

# Device prefix
DEVICE_PREFIX = "FINS_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FINS"),
        "macros": {
            "PLCNODE": 58,
        },
        "emulator": "fins",
    },
]

TEST_MODES = [TestModes.DEVSIM]


class FinsPLCTests(unittest.TestCase):
    """
    Tests for the FINS helium gas recovery PLC IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)

        self.ca.assert_that_pv_exists("FREQ", timeout=30)

        # Wait for emulator to be connected, signified by "STAT:OK"
        self.ca.assert_that_pv_is("STAT:OK", "OK")

    @skip_if_recsim("Depends on state which is not implemented in recsim")
    def test_WHEN_device_is_started_then_stopped_THEN_up_to_speed_pv_reflects_the_stopped_or_started_state(self):
        self.ca.set_pv_value("START", 1)
        self.ca.assert_that_pv_is("STAT:UP_TO_SPEED", "YES")
        self.ca.set_pv_value("STOP", 1)
        self.ca.assert_that_pv_is("STAT:UP_TO_SPEED", "NO")

