import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "CRYVALVE_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CRYVALVE"),
        "macros": {},
        "emulator": "Cryvalve",
    },
]


TEST_MODES = [TestModes.RECSIM]


class CryvalveTests(unittest.TestCase):
    """
    Tests for the Cryvalve IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Cryvalve", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_value_is_open_WHEN_get_state_THEN_state_is_open(self):
        expected_value = "OPEN"
        self.ca.set_pv_value("SIM:STAT", expected_value)

        self.ca.assert_that_pv_is("STAT", expected_value)
