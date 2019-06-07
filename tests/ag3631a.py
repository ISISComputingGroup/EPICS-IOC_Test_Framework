import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "AG3631A_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("AG3631A"),
    },
]


TEST_MODES = [TestModes.RECSIM]


class Ag3631aTests(unittest.TestCase):
    """
    Tests for the AG3631A.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(20, DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_GIVEN_voltage_set_WHEN_read_THEN_voltage_is_as_set(self):
        set_voltage = 123.456
        self.ca.set_pv_value("VOLT:SP", set_voltage)
        self.ca.assert_that_pv_is("VOLT:SP", set_voltage)

        self.ca.assert_that_pv_is("VOLT", set_voltage)
