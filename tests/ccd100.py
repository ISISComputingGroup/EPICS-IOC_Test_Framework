import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "CCD100_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CCD100"),
        "emulator": "ccd100",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class CCD100Tests(unittest.TestCase):
    """
    Tests for the CCD100.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ccd100", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_setpoint_set_WHEN_readback_THEN_readback_is_same_as_setpoint(self):
        set_point = [0, 1.23, 10]

        for point in set_point:
            self.ca.set_pv_value("READING:SP", point)
            self.ca.assert_that_pv_is("READING:SP:RBV", point)
