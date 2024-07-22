import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "MK2CHOPR_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MK2CHOPR"),
        "macros": {},
        "emulator": "Mk2Chopr",
    },
]


TEST_MODES = [TestModes.RECSIM]


class Mk2ChoprTests(unittest.TestCase):
    """
    Tests for the Mk2Chopr IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Mk2Chopr", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_frequency_set_WHEN_read_THEN_frequency_readback_is_as_expected(self):
        test_value = 10
        self.ca.set_pv_value("FREQ:SP", test_value)
        self.ca.assert_setting_setpoint_sets_readback(test_value, "FREQ", "FREQ:SP", test_value)
