import os
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list

# Device prefix
DEVICE_PREFIX = "FINS_01"

IOC_NAME = "FINS"
TEST_PATH = os.path.join(EPICS_TOP, "ioc", "master", IOC_NAME, "exampleSettings", "HELIUM_RECOVERY")

IOC_PREFIX = "{}:HE_RCVRY".format(DEVICE_PREFIX)

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

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

PV_NAMES = ["HEARTBEAT", "MCP:BANK1:TS2", "MCP:BANK1:TS1", "MCP1:BANK2:IMPURE_HE", "MCP2:BANK2:IMPURE_HE",
            "MCP1:BANK3:MAIN_HE_STORAGE", "MCP2:BANK3:MAIN_HE_STORAGE", "MCP1:BANK4:DLS_HE_STORAGE",
            "MCP2:BANK4:DLS_HE_STORAGE", "MCP1:BANK5:SPARE_STORAGE", "MCP2:BANK5:SPARE_STORAGE",
            "MCP1:BANK6:SPARE_STORAGE", "MCP2:BANK6:SPARE_STORAGE", "MCP1:BANK7:SPARE_STORAGE",
            "MCP2:BANK7:SPARE_STORAGE", "MCP1:BANK8:SPARE_STORAGE", "MCP2:BANK8:SPARE_STORAGE", "MCP:INLET:PRESSURE",
            "MCP:EXTERNAL_TEMP", "MASS_FLOW:GAS_LIQUEFACTION", "MASS_FLOW:HE_FILLS", "KAISER_COMPR:INTERNAL_TEMP",
            "COLDBOX:HE_TEMP", "COLDBOX:HE_TEMP:LIMIT", "TRANSPORT_DEWAR:PRESSURE", "HE_PURITY", "DEW_POINT"]

TEST_VALUES = range(1, len(PV_NAMES) + 1)


class HeliumRecoveryPLCTests(unittest.TestCase):
    """
    Tests for the FINS helium gas recovery PLC IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=20, device_prefix=IOC_PREFIX)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_run_function_on_device("reset")
            self._lewis.backdoor_set_on_device("connected", True)

    @parameterized.expand(parameterized_list(zip(PV_NAMES, TEST_VALUES)))
    def test_WHEN_value_set_backdoor_THEN_ioc_read_correctly(self, _, pv_name, test_value):
        self._lewis.backdoor_run_function_on_device("set_memory", (pv_name, test_value))
        self.ca.set_pv_value("SIM:{}".format(pv_name), test_value)
        self.ca.assert_that_pv_is(pv_name, test_value)
