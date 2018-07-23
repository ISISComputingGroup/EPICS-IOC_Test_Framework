import unittest
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "NGPSPSU_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("NGPSPSU"),
        "macros": {},
        "emulator": "ngpspsu",
    },
]


TEST_MODES = [TestModes.DEVSIM] #, TestModes.RECSIM]


class NgpspsuVersionTests(unittest.TestCase):
    """
    Tests for the Ngpspsu IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ngpspsu", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_that_WHEN_requested_we_THEN_get_the_version_and_firmware(self):
        # When:
        self.ca.process_pv("VERSION")

        # Then:
        self.ca.assert_that_pv_is("VERSION", "NGPS 100-50:0.9.01")

