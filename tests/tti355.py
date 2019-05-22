import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "TTI355_01"
DEVICE_NAME = "tti355"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TTI355"),
        "macros": {},
        "emulator": DEVICE_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tti355Tests(unittest.TestCase):
    """
    Tests for the Tti355 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    #def test_that_fails(self):
        #self.fail("You haven't implemented any tests!")

    def test_WHEN_voltage_is_set_THEN_voltage_setpoint_updates(self):
        for volt in [0, 1, 2]:
            self.ca.set_pv_value("VOLTAGE:SP", volt)
            self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", volt)
