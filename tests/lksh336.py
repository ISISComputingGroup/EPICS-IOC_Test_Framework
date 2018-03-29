import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "LKSH336_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LKSH336"),
        "macros": {},
        "emulator": "Lksh336",
    },
]


TEST_MODES = [TestModes.RECSIM]


class Lksh336Tests(unittest.TestCase):
    """
    Tests for the Lksh336 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Lksh336", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_temp_set_WHEN_read_THEN_temp_is_as_expected(self):
        test_value = 10
        self.ca.set_pv_value("SIM:TEMP_A", test_value)
        self.ca.assert_that_pv_is("SIM:TEMP_A", test_value)
