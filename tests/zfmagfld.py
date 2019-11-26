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

SENSOR_MATRIX_PVS = "SENSORMATRIX:{row}{column}"


class ZeroFieldMagFieldTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    @parameterized.expand(itertools.product(AXES.keys(), FIELD_STRENGTHS))
    def test_GIVEN_field_offset_THEN_field_strength_read_back_with_offset_applied(self, hw_axis, field_strength):
        self.ca.assert_setting_setpoint_sets_readback(field_strength, "{}:APPLYOFFSET".format(hw_axis),
                                                      "SIM:DAQ:{}".format(hw_axis),
                                                      expected_value=field_strength-OFFSET)

    def test_GIVEN_offset_corrected_field_WHEN_sensor_matrix_is_identity_THEN_input_field_returned_by_matrix_multiplier(self):
        offset_corrected_field = [1.1, 2.2, 3.3]
        # GIVEN
        for value, hw_axis in zip(offset_corrected_field, AXES.keys()):
            self.ca.set_pv_value("{}:OFFSET".format(hw_axis), 0)
            self.ca.set_pv_value("SIM:DAQ:{}".format(hw_axis), value)

        # WHEN
        for i in range(3):
            for j in range(3):
                self.ca.set_pv_value(SENSOR_MATRIX_PVS.format(row=i+1, column=j+1), 1 if i == j else 0)

        # THEN
        for value, hw_axis in zip(offset_corrected_field, AXES.keys()):
            self.ca.assert_that_pv_is_number("{}:CORRECTEDFIELD".format(hw_axis), value, tolerance=0.1*abs(value))
