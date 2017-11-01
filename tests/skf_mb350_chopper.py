import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# List of chopper crates that tests should use.
CRATES = [1, 2]

# Device prefix
DEVICE_PREFIX = "SKFMB350_01"


class Skf_mb350_chopperTests(unittest.TestCase):
    """
    Tests for the SKF MB350 Chopper IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("skf_mb350_chopper")
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

        # Ensure PVs for all crates are up.
        for crate in CRATES:
            self.ca.wait_for("{}:FREQ".format(crate), timeout=30)

    def test_fail(self):
        self.ca.assert_that_pv_is_number("1:FREQ", 2.1, 0.01)

    def test_pass(self):
        self.ca.assert_that_pv_is_number("1:FREQ", 2.0, 0.01)

