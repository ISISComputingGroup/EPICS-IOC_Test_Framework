import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "MKSPR4KB_01"
EMULATOR_NAME = "mkspr4kb"

HE3POT_COARSE_TIME = 20
DRIFT_BUFFER_SIZE = 20

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MKSPR4KB"),
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


CHANNELS = ("CH1", "CH2")


class MKS_PR4000B_Tests(unittest.TestCase):
    """
    Tests for the MKSPR4K IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(CHANNELS))
    def test_WHEN_ioc_is_started_THEN_channels_are_not_disabled(self, _, chan):
        self.ca.assert_that_pv_is("{}:DISABLE".format(chan), "COMMS ENABLED")
