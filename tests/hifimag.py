import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "HIFIMAG_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HIFIMAG"),
    },
]


TEST_MODES = [TestModes.RECSIM]


class HifimagTests(unittest.TestCase):
    """
    Tests for the HIFIMAG.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(20, DEVICE_PREFIX)
        self.ca.wait_for("DISABLE", timeout=30)
        
    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_GIVEN_setpoint1_set_WHEN_read_THEN_setpoint1_is_as_set(self):
        set_point1 = 1.234
        self.ca.set_pv_value("1:SETPOINT:SP", set_point1)
        self.ca.assert_that_pv_is("1:SETPOINT:SP", set_point1)
        
        self.ca.assert_that_pv_is("1:SETPOINT", set_point1)
