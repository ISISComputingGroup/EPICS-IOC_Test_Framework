import unittest
import itertools

from parameterized import parameterized
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir

DEVICE_PREFIX = "ZFMAGFLD_01"

TEST_MODES = [TestModes.RECSIM]

OFFSET = 1.1

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ZFMAGFLD"),
        "macros": {
                   "OFFSET_X": OFFSET,
                   "OFFSET_Y": OFFSET,
                   "OFFSET_Z": OFFSET
                   }
    },
]

AXES = {"X": "L",
        "Y": "T",
        "Z": "V"}

FIELD_STRENGTHS = [0.0, 1.1, 12.3, -1.1, -12.3]


class ZeroFieldMagFieldTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    @parameterized.expand(itertools.product(AXES.keys(), FIELD_STRENGTHS))
    def test_GIVEN_field_offset_THEN_field_strength_read_back_with_offset_applied(self, hw_axis, field_strength):
        self.ca.assert_setting_setpoint_sets_readback(field_strength, "{}:OFFSET".format(hw_axis),
                                                      "SIM:DAQ:{}".format(hw_axis),
                                                      expected_value=field_strength-OFFSET)
