import unittest
import os
from unittest import skip

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import ProcServLauncher
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "SIMPLE"

EPICS_ROOT = os.getenv("EPICS_KIT_ROOT")

IOCS = [
    {
        "LAUNCHER": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": os.path.realpath(os.path.join(EPICS_ROOT, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple")),
        "macros": {},
    },
]


TEST_MODES = [None, ]


class SimpleTests(unittest.TestCase):
    """
    Tests for the Simple IOC
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Simple", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    @skip("This test is not ready yet")
    def test_that_always_passes(self):
        pass

