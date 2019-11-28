import unittest
import itertools

from parameterized import parameterized
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
import numpy as np

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
        self.write_offset(0)

    def write_offset(self, value_to_set):
        """ Writes the same offset to all three components"""
        for axis in AXES.keys():
            print('Set {} to {}'.format("{}:OFFSET".format(axis), value_to_set))
            self.ca.set_pv_value("{}:OFFSET".format(axis), value_to_set)

    @parameterized.expand(itertools.product(AXES.keys(), FIELD_STRENGTHS))
    def test_GIVEN_field_offset_THEN_field_strength_read_back_with_offset_applied(self, hw_axis, field_strength):
        self.write_offset(OFFSET)

        self.ca.assert_setting_setpoint_sets_readback(field_strength, "{}:APPLYOFFSET".format(hw_axis),
                                                      "SIM:DAQ:{}".format(hw_axis),
                                                      expected_value=field_strength-OFFSET)

    def test_GIVEN_offset_corrected_field_WHEN_sensor_matrix_is_identity_THEN_input_field_returned_by_matrix_multiplier(self):
        offset_corrected_field = [1.1, 2.2, 3.3]
        # GIVEN
        for value, hw_axis in zip(offset_corrected_field, AXES.keys()):
            self.ca.set_pv_value("SIM:DAQ:{}".format(hw_axis), value)

        # WHEN
        for i in range(3):
            for j in range(3):
                self.ca.set_pv_value(SENSOR_MATRIX_PVS.format(row=i+1, column=j+1), 1 if i == j else 0)

        # THEN
        for value, hw_axis in zip(offset_corrected_field, AXES.keys()):
            self.ca.assert_that_pv_is_number("{}:CORRECTEDFIELD".format(hw_axis), value, tolerance=0.1*abs(value))

    @parameterized.expand(['X', 'Y', 'Z'])
    def test_GIVEN_sensor_matrix_with_only_one_nonzero_column_THEN_corrected_field_has_component_in_correct_dimension(self, hw_axis):
        print('\n'+hw_axis)
        input_field = {"X": 1.1,
                       "Y": 2.2,
                       "Z": 3.3}

        for component in AXES.keys():
            print('setting {} to {}'.format(component, input_field[component]))
            self.ca.set_pv_value("SIM:DAQ:{}".format(component), input_field[component])

        # GIVEN
        sensor_matrix = np.zeros((3, 3))

        # Set one non-diagnoal element to 1
        if hw_axis == "X":
            sensor_matrix[0, :] = 1
        elif hw_axis == "Y":
            sensor_matrix[1, :] = 1
        elif hw_axis == "Z":
            sensor_matrix[2, :] = 1

        import pprint
        pprint.pprint(sensor_matrix)

        # WHEN
        for i in range(3):
            for j in range(3):
                self.ca.set_pv_value(SENSOR_MATRIX_PVS.format(row=i+1, column=j+1), sensor_matrix[i, j])

        for component in ['X', 'Y', 'Z']:
            print(component, self.ca.get_pv_value("{}:CORRECTEDFIELD".format(component)))

        # THEN
        for component in AXES.keys():
            if component == hw_axis:
                expected_value = sum(input_field.values())
            else:
                expected_value = 0

            self.ca.assert_that_pv_is_number("{}:CORRECTEDFIELD".format(component), expected_value)

    def test_GIVEN_measured_data_WHEN_corrections_applied_THEN_field_magnitude_read_back(self):
        # GIVEN
        input_field = {"X": 2.2,
                       "Y": 3.3,
                       "Z": 4.4}

        for component in AXES.keys():
            self.ca.set_pv_value("SIM:DAQ:{}".format(component), input_field[component])

        self.write_offset(OFFSET)

        sensor_matrix = np.array([-1.17e-1, 7.36e-2, -2e-1, -3.41e-1, -2.15e-1, -3e-1, -2.3e-1, -4e-2, 1e-1], order='C').reshape(3, 3, order='C')
        #sensor_matrix = np.array([1,1,1,0,0,0,0,0,0], order='C').reshape(3, 3, order='C')

        import pprint
        pprint.pprint(sensor_matrix)

        for i in range(3):
            for j in range(3):
                print('setting {} to {}'.format(SENSOR_MATRIX_PVS.format(row=i+1, column=j+1), sensor_matrix[i, j]))
                self.ca.set_pv_value(SENSOR_MATRIX_PVS.format(row=i+1, column=j+1), sensor_matrix[i, j], wait=False)
                print('AFDS', self.ca.get_pv_value('{}:APPLYOFFSET.B'.format(component)))


        offset_data = {}

        value = 0.0
        iocval = {}
        for axis in AXES.keys():
            offset_data[axis] = input_field[axis] - OFFSET

            component = self.ca.get_pv_value("{}:CORRECTEDFIELD".format(axis))
            iocval[axis] = component
            print('{} from ioc is {}'.format(axis, component))
            value += component * component

        print(np.sqrt(value))

        expected_fields = np.matmul(sensor_matrix, np.array([input_field['X']-OFFSET, input_field['Y']-OFFSET, input_field['Z']-OFFSET]))

        print(expected_fields)

        expected_magnitude = np.linalg.norm(expected_fields)

        self.ca.assert_that_pv_is_number("FIELDSTRENGTH", expected_magnitude, tolerance=0.1*expected_magnitude)
