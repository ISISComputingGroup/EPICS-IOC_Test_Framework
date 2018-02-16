import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes

from utils.testing import get_running_lewis_and_ioc

# Device prefix
DEVICE_PREFIX = "SKFCHOPPER_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SKFCHOPPER"),
        "macros": {
            "NAME": "TEST_CHOPPER",
            "OPEN": 127.8,
            "CLOSED": 307.8,
        },
    },
]

TEST_MODES = [TestModes.RECSIM]


class SkfG5ChopperTests(unittest.TestCase):
    """
    Tests for the SKF G5 Chopper Controller

    RECSIM is not currently compatible with Asyn, so the only possible test
    is to check for the presence of a specific PV and therefore that the
    DB file has loaded correctly.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_state_WHEN_read_THEN_state_is_as_expected(self):
        expected_state = "Invalid"

        self.ca.assert_that_pv_is("STATE", expected_state)
