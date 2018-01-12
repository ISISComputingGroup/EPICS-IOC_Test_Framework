import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister

from utils.testing import get_running_lewis_and_ioc

# MACROS to use for the IOC
MACROS = {"NAME": "TEST_CHOPPER", "OPEN": 127.8, "CLOSED": 307.8}

# Device prefix
DEVICE_PREFIX = "SKFCHOPPER_01"


class Skf_g5_chopperTests(unittest.TestCase):
    """
    Tests for the SKF G5 Chopper Controller

    RECSIM is not currently compatible with Asyn, so the only possible test
    is to check for the presence of a specific PV and therefore that the
    DB file has loaded correctly.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("skf_g5_chopper")

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_state_WHEN_read_THEN_state_is_as_expected(self):
        expected_state = "Invalid"

        self.ca.assert_that_pv_is("STATE", expected_state)
