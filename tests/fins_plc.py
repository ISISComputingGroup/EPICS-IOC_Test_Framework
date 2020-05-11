import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
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

MEMORY_FIELD_MAPPING = {
        19500: 1,  # heartbeat
        19533: 999,  # helium purity
        19534: 5,  # dew point
        19900: 100  # HE_BAG_PR_BE_ATM
    }

class FinsPLCTests(unittest.TestCase):
    """
    Tests for the FINS helium gas recovery PLC IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_run_function_on_device("reset")
            self._lewis.backdoor_set_on_device("connected", True)

    def test_WHEN_heartbeat_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device()

    @skip_if_recsim("Depends on state which is not implemented in recsim")
    def test_WHEN_device_is_started_then_stopped_THEN_up_to_speed_pv_reflects_the_stopped_or_started_state(self):
        self.ca.set_pv_value("START", 1)
        self.ca.assert_that_pv_is("STAT:UP_TO_SPEED", "YES")
        self.ca.set_pv_value("STOP", 1)
        self.ca.assert_that_pv_is("STAT:UP_TO_SPEED", "NO")

