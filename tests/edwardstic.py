import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

from parameterized import parameterized

DEVICE_PREFIX = "EDTIC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("EDTIC"),
        "macros": {},
        "emulator": "edwardstic",
    },
]

# No recsim as this device makes heavy use of record redirection
TEST_MODES = [TestModes.DEVSIM, ]


class EdwardsTICTests(unittest.TestCase):
    """
    Tests for the Edwards Turbo Instrument Controller (TIC) IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("edwardstic", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("is_connected", True)

    def test_GIVEN_turbo_pump_switched_on_WHEN_status_requested_THEN_status_reads_switched_on(self):
        # GIVEN
        self.ca.set_pv_value("TURBO:START", "On", wait=True)

        # THEN
        self.ca.assert_that_pv_is("TURBO:STA", "Running")

    def test_GIVEN_disconnected_device_WHEN_pump_status_read_THEN_PVs_read_invalid(self):
        # GIVEN
        self._lewis.backdoor_set_on_device("is_connected", False)

        # WHEN
        self.ca.assert_that_pv_alarm_is("TURBO:STA", self.ca.Alarms.INVALID)
