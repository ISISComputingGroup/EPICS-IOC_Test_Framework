import unittest
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import IOCRegister


DEVICE_PREFIX = "FINS_01"
ioc_name = "FINS"
test_path = os.path.join(EPICS_TOP, "ioc", "master", ioc_name, "exampleSettings", "LARMOR_bench")

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir(ioc_name),
        "pv_for_existence": "BENCH:FLOW1",
        "macros": {
            "FINSCONFIGDIR": test_path.replace("\\", "/"),
            "PLCIP": "127.0.0.1"
        },
    },
]


TEST_MODES = [TestModes.RECSIM]


class FinsTests(unittest.TestCase):
    """
    Tests for the Fins IOC.
    """
    def setUp(self):
        self._ioc = IOCRegister.get_running("FINS_01")
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_fins_THEN_has_flow_pv(self):
        self.ca.assert_that_pv_exists("BENCH:FLOW1")

