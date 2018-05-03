import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "LKSH218_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LKSH218"),
        "macros": {},
        "emulator": "Lksh218",
    },
]


TEST_MODES = [TestModes.RECSIM]


class Lksh218Tests(unittest.TestCase):
    """
    Tests for the Lksh218 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Lksh218", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_temp_set__WHEN_read_THEN_temp_is_as_expected(self):
        test_value = 50
        self.ca.set_pv_value("SIM:TEMP1", test_value)
        self.ca.assert_that_pv_is("SIM:TEMP1", test_value)
        