import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, skip_if_devsim


DEVICE_PREFIX = "FINS_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FINS"),
        "macros": { "PLCIP" : "127.0.0.1" },
        "emulator": "Fins",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class FinsTests(unittest.TestCase):
    """
    Tests for the Fins IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Fins", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    @skip_if_devsim("In dev sim this test fails")
    def test_GIVEN_fins_THEN_has_flow_pv(self):
        self.ca.assert_that_pv_is_not("BENCH:FLOW1", "")

