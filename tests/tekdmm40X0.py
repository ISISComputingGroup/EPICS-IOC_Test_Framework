import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "TEKDMM40X0_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TEKDMM40X0"),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM]


class tekdmm40X0Tests(unittest.TestCase):
    """
    Tests for the Pdr2000 IOC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")
