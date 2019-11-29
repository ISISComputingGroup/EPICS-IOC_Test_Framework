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
SENSOR_MATRIX_SIZE = 3


class ZeroFieldMagFieldTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)
        self.write_offset(0)

    def write_offset(self, offset):
        """
        Writes offset values for all three IOC components
        Args:
            offset: float, the offset to be written to the IOC

        Returns:
            None

        """
        for axis in AXES.keys():
            self.ca.set_pv_value("{}:OFFSET".format(axis), offset)

    def write_sensor_matrix(self, sensor_matrix):
        """
        Writes the provided sensor matrix to the relevant PVs

        Args:
            sensor_matrix: 3x3 numpy ndarray containing the values to use as the fixed sensor matrix.

        Returns:
            None
        """
        assert sensor_matrix.shape == (SENSOR_MATRIX_SIZE, SENSOR_MATRIX_SIZE)

        for i in range(SENSOR_MATRIX_SIZE):
            for j in range(SENSOR_MATRIX_SIZE):
                self.ca.set_pv_value(SENSOR_MATRIX_PVS.format(row=i+1, column=j+1), sensor_matrix[i, j])

    def apply_offset_to_field(self, simulated_field, offset):
        """
        Applies offset to the simulated measured field

        Args:
            simulated_field: dict with 'X', 'Y' and 'Z' keys. Values are the corresponding simulated field values
            offset: float, The offset to subtract from the input data. Applies same offset to all fields

        Returns:
            offset_applied_field: dict with 'X', 'Y', 'Z' keys. Values are offset-subtracted simulated_field values

        """

        offset_applied_field = {}
        for axis in AXES.keys():
            offset_applied_field[axis] = simulated_field[axis] - offset

        return offset_applied_field

    def write_simulated_field_values(self, simulated_field):
        """
        Writes the given simulated field values to the IOC

        Args:
            simulated_field: dict with 'X', 'Y' and 'Z' keys. Values are the corresponding simulated field values

        Returns:
            None

        """

        for component in AXES.keys():
            self.ca.set_pv_value("SIM:DAQ:{}".format(component), simulated_field[component])

    def apply_offset_and_matrix_multiplication(self, simulated_field, offset, sensor_matrix):
        """
        Applies trasformation between raw or 'measured' field to 'corrected' field.

        Subtracts the offset from the input (raw) data, then matrix multiplies by the sensor matrix.

        Args:
            simulated_field: dict with keys matching AXES (X, Y and Z). Values are the simulated field values
            offset: float, The Offset to subtract from the input data. Applies same offset to all fields
            sensor_matrix: 3x3 numpy ndarray containing the values to use as the fixed sensor matrix.

        Returns:
            corrected_field_vals: 3-element array containing corrected X, Y and Z field values

        """

        offset_input_field = self.apply_offset_to_field(simulated_field, offset)

        corrected_field_vals = np.matmul(sensor_matrix, np.array([offset_input_field["X"],
                                                                  offset_input_field["Y"],
                                                                  offset_input_field["Z"]]))

        return corrected_field_vals

    @parameterized.expand(itertools.product(AXES.keys(), FIELD_STRENGTHS))
    def test_GIVEN_field_offset_THEN_field_strength_read_back_with_offset_applied(self, hw_axis, field_strength):
        # GIVEN
        self.write_offset(OFFSET)

        # THEN
        self.ca.assert_setting_setpoint_sets_readback(field_strength, "{}:APPLYOFFSET".format(hw_axis),
                                                      "SIM:DAQ:{}".format(hw_axis),
                                                      expected_value=field_strength-OFFSET)

    def test_GIVEN_offset_corrected_field_WHEN_sensor_matrix_is_identity_THEN_input_field_returned_by_matrix_multiplier(self):
        offset_corrected_field = [1.1, 2.2, 3.3]
        # GIVEN
        for value, hw_axis in zip(offset_corrected_field, AXES.keys()):
            self.ca.set_pv_value("SIM:DAQ:{}".format(hw_axis), value)

        # WHEN
        self.write_sensor_matrix(np.identity(3))

        # THEN
        for value, hw_axis in zip(offset_corrected_field, AXES.keys()):
            self.ca.assert_that_pv_is_number("{}:CORRECTEDFIELD".format(hw_axis), value, tolerance=0.1*abs(value))

    @parameterized.expand(['X', 'Y', 'Z'])
    def test_GIVEN_sensor_matrix_with_only_one_nonzero_row_THEN_corrected_field_has_component_in_correct_dimension(self, hw_axis):

        input_field = {"X": 1.1,
                       "Y": 2.2,
                       "Z": 3.3}

        self.write_simulated_field_values(input_field)

        # GIVEN
        sensor_matrix = np.zeros((3, 3))

        # Set one row to one
        if hw_axis == "X":
            sensor_matrix[0, :] = 1
        elif hw_axis == "Y":
            sensor_matrix[1, :] = 1
        elif hw_axis == "Z":
            sensor_matrix[2, :] = 1

        # WHEN
        self.write_sensor_matrix(sensor_matrix)

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

        sensor_matrix = np.array([-1.17e-1, 7.36e-2, -2e-1,
                                  -3.41e-1, -2.15e-1, -3e-1,
                                  -2.3e-1, -4e-2, 1e-1]).reshape(3, 3)

        self.write_simulated_field_values(input_field)
        self.write_offset(OFFSET)
        self.write_sensor_matrix(sensor_matrix)

        # THEN
        expected_field_vals = self.apply_offset_and_matrix_multiplication(input_field, OFFSET, sensor_matrix)

        expected_magnitude = np.linalg.norm(expected_field_vals)

        self.ca.assert_that_pv_is_number("FIELDSTRENGTH", expected_magnitude, tolerance=0.1*expected_magnitude)
