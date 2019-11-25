import unittest

from parameterized import parameterized
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir

DEVICE_PREFIX = "ZFMAGFLD_01"

TEST_MODES = [TestModes.RECSIM]

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ZFMAGFLD"),
    },
]


class ZeroFieldMagFieldTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    @parameterized.expand([
        ("X", "L"),
        ("Y", "T"),
        ("Z", "V"),
    ])
    def test_GIVEN_X_field_strength_THEN_field_strength_read_back(self, hw_axis, user_axis):
        field_strength = 12.3
        self.ca.assert_setting_setpoint_sets_readback(field_strength, user_axis, "SIM:DAQ:{}".format(hw_axis))
