import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
import os


DEVICE_PREFIX = "MERCURY_01"
EPICS_TOP = os.environ.get("KIT_ROOT", os.path.join("C:\\", "Instrument", "Apps", "EPICS"))

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "MERCURY_ITC", "iocBoot", "iocMERCURY-IOC-01"),
        "macros": {},
        "emulator": "Mercury",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]




class MercuryTests(unittest.TestCase):
    """
    Tests for the Mercury IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Mercury", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_that_fails(self):
        self.fail("You haven't implemented any tests!")
