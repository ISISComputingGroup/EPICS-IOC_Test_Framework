import os
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, skip_if_devsim

# Device prefix
DEVICE_PREFIX = "FINS_01"

IOC_NAME = "FINS"
TEST_PATH = os.path.join(EPICS_TOP, "ioc", "master", IOC_NAME, "exampleSettings", "HELIUM_RECOVERY")

IOC_PREFIX = "{}:HE-RCVRY".format(DEVICE_PREFIX)

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FINS"),
        "custom_prefix": IOC_PREFIX,
        "macros": {
            "FINSCONFIGDIR": TEST_PATH.replace("\\", "/"),
            "PLCIP": "127.0.0.1",
            "PLCNODE": 58,
        },
        "emulator": "fins",
    },
]

TEST_MODES = [TestModes.RECSIM]


class FinsPLCTests(unittest.TestCase):
    """
    Tests for the FINS helium gas recovery PLC IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, device_prefix=IOC_PREFIX)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_run_function_on_device("reset")
            self._lewis.backdoor_set_on_device("connected", True)

    @skip_if_recsim("Lewis backdoor does not work in recsim")
    def test_WHEN_heartbeat_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("heartbeat", 1)
        self.ca.assert_that_pv_is("HEARTBEAT", 1)

    @skip_if_devsim("sim records are not used in devsim")
    def test_WHEN_heartbeat_set_backdoor_THEN_ioc_read_correctly(self):
        self.ca.set_pv_value("SIM:HEARTBEAT", 1)
        self.ca.assert_that_pv_is("HEARTBEAT", 1)

    @skip_if_recsim("Lewis backdoor does not work in recsim")
    def test_WHEN_helium_purity_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("helium_purity", 2)
        self.ca.assert_that_pv_is("HE_PURITY", 2)

    @skip_if_recsim("Lewis backdoor does not work in recsim")
    def test_WHEN_dew_point_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("dew_point", 3)
        self.ca.assert_that_pv_is("DEW_POINT", 3)

    @skip_if_recsim("Lewis backdoor does not work in recsim")
    def test_WHEN_he_bag_pr_be_atm_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("he_bag_pr_be_atm", 4)
        self.ca.assert_that_pv_is("HE_BAG_PR_BE_ATM", 4)
