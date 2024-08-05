import itertools
import time
import unittest

import numpy as np
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list

DEVICE_PREFIX = "ZFMAGFLD_01"
DEVICE_PREFIX_2 = "ZFMAGFLD_02"

TEST_MODES = [TestModes.RECSIM]

OFFSET = 1.3

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ZFMAGFLD"),
        "ioc_launcher_class": ProcServLauncher,
    },
]

AXES = {"X": "L", "Y": "T", "Z": "V"}

ZERO_FIELD = {"X": 0.0, "Y": 0.0, "Z": 0.0}

FIELD_STRENGTHS = [0.0, 1.1, 12.3, -1.1, -12.3]

SENSOR_MATRIX_PVS = "SENSORMATRIX:{row}{column}"
SENSOR_MATRIX_SIZE = 3

PVS_WHICH_USE_DAQ_DATA = [
    "OVERLOAD",
    "FIELDSTRENGTH",
    "MEASURED:X",
    "MEASURED:Y",
    "MEASURED:Z",
    "CORRECTEDFIELD:X",
    "CORRECTEDFIELD:Y",
    "CORRECTEDFIELD:Z",
]


class ZeroFieldMagFieldTests(unittest.TestCase):
    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)
        self.write_offset(0)
        self.ca.set_pv_value("RANGE", 1.0, sleep_after_set=0.0)
        self.write_simulated_field_values(ZERO_FIELD)
        self.write_simulated_alarm_level(self.ca.Alarms.NONE)
        self.ca.process_pv("TAKEDATA")

    def write_offset(self, offset):
        """
        Writes offset values for all three IOC components
        Args:
            offset: float, the offset to be written to the IOC

        Returns:
            None

        """
        for axis in AXES.keys():
            self.ca.set_pv_value("OFFSET:{}".format(axis), offset, sleep_after_set=0.0)

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
                self.ca.set_pv_value(
                    SENSOR_MATRIX_PVS.format(row=i + 1, column=j + 1),
                    sensor_matrix[i, j],
                    sleep_after_set=0.0,
                )

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
        Writes the given simulated field values to the IOC.

        Also asserts that the value has been taken up by the '_RAW' PV. We need to do this because the '_RAW' PVs are
        on SCAN = .1 second in RECSIM, so some time is taken between writing the SIM field and it being available in the
        '_RAW' PV.

        Args:
            simulated_field: dict with 'X', 'Y' and 'Z' keys. Values are the corresponding simulated field values

        Returns:
            None

        """

        for component in AXES.keys():
            self.ca.set_pv_value(
                "SIM:DAQ:{}".format(component), simulated_field[component], sleep_after_set=0.0
            )
            self.ca.assert_that_pv_is_number(
                "DAQ:{}:_RAW".format(component), simulated_field[component]
            )

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

        corrected_field_vals = np.matmul(
            sensor_matrix,
            np.array([offset_input_field["X"], offset_input_field["Y"], offset_input_field["Z"]]),
        )

        return corrected_field_vals

    def get_overload_range_value(self):
        """
        Returns the maximum value an input field can have before the magnetometer is overloaded
        """

        return self.ca.get_pv_value("RANGE") * 4.5

    def write_simulated_alarm_level(self, level):
        """
        Writes to the SIML field of the RAW data pvs. This sets the severity level of the three pvs to level.
        Waits for the SEVR fields of the RAW data pvs to update before returning.

        Args:
            level: Class attribute of ChannelAccess.Alarms (e.g. ca.Alarms.NONE). The severity level to set to the PV

        """
        for axis in AXES.keys():
            self.ca.set_pv_value("DAQ:{}:_RAW.SIMS".format(axis), level, sleep_after_set=0.0)

        # Wait for the raw PVs to process
        for axis in AXES.keys():
            self.ca.assert_that_pv_alarm_is("DAQ:{}:_RAW".format(axis), level)

    @parameterized.expand(parameterized_list(itertools.product(AXES.keys(), FIELD_STRENGTHS)))
    def test_GIVEN_field_offset_THEN_field_strength_read_back_with_offset_applied(
        self, _, hw_axis, field_strength
    ):
        # GIVEN
        self.write_offset(OFFSET)

        field = {"X": 0, "Y": 0, "Z": 0}

        field[hw_axis] = field_strength

        self.write_simulated_field_values(field)
        self.ca.set_pv_value("SIM:DAQ:{}".format(hw_axis), field_strength, sleep_after_set=0.0)

        # WHEN
        self.ca.process_pv("TAKEDATA")

        # THEN
        self.ca.assert_that_pv_is_number("APPLYOFFSET:{}".format(hw_axis), field_strength - OFFSET)

    def test_GIVEN_offset_corrected_field_WHEN_sensor_matrix_is_identity_THEN_input_field_returned_by_matrix_multiplier(
        self,
    ):
        offset_corrected_field = {"X": 1.1, "Y": 2.2, "Z": 3.3}

        # GIVEN
        self.write_simulated_field_values(offset_corrected_field)

        # WHEN
        self.write_sensor_matrix(np.identity(3))
        self.ca.process_pv("TAKEDATA")

        # THEN
        for hw_axis in AXES.keys():
            expected_value = offset_corrected_field[hw_axis]
            self.ca.assert_that_pv_is_number(
                "CORRECTEDFIELD:{}".format(hw_axis),
                expected_value,
                tolerance=0.1 * abs(expected_value),
            )

            self.ca.assert_that_pv_alarm_is(
                "CORRECTEDFIELD:{}".format(hw_axis), self.ca.Alarms.NONE
            )

    @parameterized.expand(parameterized_list(["X", "Y", "Z"]))
    def test_GIVEN_sensor_matrix_with_only_one_nonzero_row_THEN_corrected_field_has_component_in_correct_dimension(
        self, _, hw_axis
    ):
        input_field = {"X": 1.1, "Y": 2.2, "Z": 3.3}

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
        self.ca.process_pv("TAKEDATA")

        # THEN
        for component in AXES.keys():
            if component == hw_axis:
                expected_value = sum(input_field.values())
            else:
                expected_value = 0

            self.ca.assert_that_pv_is_number("CORRECTEDFIELD:{}".format(component), expected_value)

    def test_GIVEN_test_input_field_strengths_WHEN_corrections_applied_THEN_corrected_fields_agree_with_labview(
        self,
    ):
        # GIVEN
        input_field = {"X": 11.1, "Y": 22.2, "Z": 33.3}

        input_offsets = {"X": -8.19e-1, "Y": 3.45e-1, "Z": -6.7e-1}

        sensor_matrix = np.array(
            [-1.17e-1, 7.36e-2, -2e-1, -3.41e-1, -2.15e-1, -3e-1, -2.3e-1, -4e-2, 1e-1]
        ).reshape(3, 3)

        self.write_simulated_field_values(input_field)
        self.write_sensor_matrix(sensor_matrix)

        for axis in input_offsets.keys():
            self.ca.set_pv_value("OFFSET:{}".format(axis), input_offsets[axis], sleep_after_set=0.0)

        # WHEN
        self.ca.process_pv("TAKEDATA")

        # THEN
        labview_result = {"X": -6.58, "Y": -18.9542, "Z": -0.21857}

        for component in AXES.keys():
            self.ca.assert_that_pv_is_number(
                "CORRECTEDFIELD:{}".format(component), labview_result[component], tolerance=1e-4
            )

    def test_GIVEN_measured_data_WHEN_corrections_applied_THEN_field_magnitude_read_back(self):
        # GIVEN
        input_field = {"X": 2.2, "Y": 3.3, "Z": 4.4}

        sensor_matrix = np.array(
            [-1.17e-1, 7.36e-2, -2e-1, -3.41e-1, -2.15e-1, -3e-1, -2.3e-1, -4e-2, 1e-1]
        ).reshape(3, 3)

        self.write_simulated_field_values(input_field)
        self.write_offset(OFFSET)
        self.write_sensor_matrix(sensor_matrix)

        # WHEN
        self.ca.process_pv("TAKEDATA")

        # THEN
        expected_field_vals = self.apply_offset_and_matrix_multiplication(
            input_field, OFFSET, sensor_matrix
        )

        expected_magnitude = np.linalg.norm(expected_field_vals)

        self.ca.assert_that_pv_is_number(
            "FIELDSTRENGTH", expected_magnitude, tolerance=0.1 * expected_magnitude, timeout=30
        )

    def test_GIVEN_no_forced_scans_WHEN_takedata_alias_processed_THEN_all_magnetometer_axes_read_and_processed(
        self,
    ):
        # GIVEN
        test_field = {"X": 1.1, "Y": 2.2, "Z": 3.3}

        with self._ioc.start_with_macros({"FORCED_SCAN": "NO"}, pv_to_wait_for="DISABLE"):
            self.write_simulated_field_values(test_field)

            time.sleep(1)

            for component in AXES.keys():
                self.ca.assert_that_pv_is_not_number(
                    "DAQ:{}".format(component), test_field[component]
                )

            # WHEN
            self.ca.process_pv("TAKEDATA")

            # THEN
            for component in AXES.keys():
                self.ca.assert_that_pv_is_number(
                    "DAQ:{}".format(component),
                    test_field[component],
                    tolerance=0.1 * test_field[component],
                )

    def test_GIVEN_forced_scans_WHEN_fields_change_THEN_all_magnetometer_axes_read_and_processed_automatically(
        self,
    ):
        # GIVEN
        test_field = {"X": 1.1, "Y": 2.2, "Z": 3.3}

        with self._ioc.start_with_macros({"FORCED_SCAN": "YES"}, pv_to_wait_for="DISABLE"):
            # WHEN

            self.write_simulated_field_values(test_field)

            # THEN
            for component in AXES.keys():
                self.ca.assert_that_pv_is_number(
                    "DAQ:{}".format(component),
                    test_field[component],
                    tolerance=0.1 * test_field[component],
                )

    @parameterized.expand(parameterized_list(FIELD_STRENGTHS))
    def test_GIVEN_magnetometer_scaling_factor_WHEN_data_read_THEN_inputs_scaled_by_factor(
        self, _, factor
    ):
        # GIVEN
        self.ca.set_pv_value("RANGE", factor, sleep_after_set=0.0)

        test_field = {"X": 1.1, "Y": 2.2, "Z": 3.3}

        self.write_simulated_field_values(test_field)

        self.ca.process_pv("TAKEDATA")

        # THEN
        for component in AXES.keys():
            self.ca.assert_that_pv_is_number(
                "MEASURED:{}".format(component), test_field[component] * factor
            )

    @parameterized.expand(parameterized_list(AXES.keys()))
    def test_GIVEN_measured_field_too_high_THEN_overload_pv_reads_true_and_is_in_alarm(
        self, _, axis
    ):
        # GIVEN
        test_field = {"X": 1.1, "Y": 1.1, "Z": 1.1}

        test_field[axis] = self.ca.get_pv_value("RANGE") * 4.5 + 1.0

        # WHEN
        self.write_simulated_field_values(test_field)
        self.ca.process_pv("TAKEDATA")

        # THEN
        self.ca.assert_that_pv_is("OVERLOAD", "OVERLOADED")
        self.ca.assert_that_pv_alarm_is("OVERLOAD", self.ca.Alarms.MAJOR)

    def test_GIVEN_measured_field_in_range_THEN_overload_pv_reads_false_and_not_in_alarm(self):
        # GIVEN
        test_value = self.get_overload_range_value() - 1.0

        test_field = {"X": test_value, "Y": test_value, "Z": test_value}

        # WHEN
        self.write_simulated_field_values(test_field)
        self.ca.process_pv("TAKEDATA")

        # THEN
        self.ca.assert_that_pv_is("OVERLOAD", "NORMAL")
        self.ca.assert_that_pv_alarm_is("OVERLOAD", self.ca.Alarms.NONE)

    def test_GIVEN_field_overloaded_THEN_output_PVs_in_major_alarm(self):
        # GIVEN
        overload_value = self.get_overload_range_value() + 1.0

        test_field = {"X": overload_value, "Y": overload_value, "Z": overload_value}

        self.write_simulated_field_values(test_field)

        self.ca.process_pv("TAKEDATA")

        # THEN
        self.ca.assert_that_pv_alarm_is("FIELDSTRENGTH", self.ca.Alarms.MAJOR)
        for axis in AXES.keys():
            self.ca.assert_that_pv_alarm_is("CORRECTEDFIELD:{}".format(axis), self.ca.Alarms.MAJOR)

    @parameterized.expand(
        parameterized_list(
            itertools.product(
                [
                    ChannelAccess.Alarms.INVALID,
                    ChannelAccess.Alarms.MAJOR,
                    ChannelAccess.Alarms.MAJOR,
                ],
                PVS_WHICH_USE_DAQ_DATA,
            )
        )
    )
    def test_GIVEN_raw_daq_pvs_in_alarm_WHEN_PVs_processed_THEN_alarm_copied_to_downstream_pvs(
        self, _, alarm, pv
    ):
        # GIVEN
        self.ca.assert_that_pv_alarm_is("{}.SEVR".format(pv), self.ca.Alarms.NONE)

        self.write_simulated_alarm_level(alarm)

        self.ca.process_pv("TAKEDATA")

        # THEN
        self.ca.assert_that_pv_alarm_is("{}.SEVR".format(pv), alarm)

    @parameterized.expand(parameterized_list(AXES.keys()))
    def test_GIVEN_smoothing_samples_WHEN_setting_field_THEN_average_field_is_given(self, _, axis):
        # In sim mode 1 sample every 0.1s. 15s should be slow enough to avoid any races between the tests and the ioc,
        # but fast enough not to slow down the whole test suite unnecessarily.
        number_samples = 150

        full_averaging_time = number_samples * 0.1  # 0.1s is the update rate in sim mode.

        field_number = 100
        pv = "DAQ:{}".format(axis)
        with self._ioc.start_with_macros({"NUM_SAMPLES": number_samples}, pv_to_wait_for=pv):
            field = {"X": 0, "Y": 0, "Z": 0}
            self.write_simulated_field_values(field)

            # make sure the field is 0
            self.ca.assert_that_pv_is_number("DAQ:{}:_RAW".format(axis), 0, full_averaging_time + 5)
            self.ca.process_pv("TAKEDATA")
            self.ca.assert_that_pv_is_number(pv, 0)

            # Change the field number
            field[axis] = field_number
            self.write_simulated_field_values(field)

            self.ca.assert_that_pv_value_is_increasing(
                "DAQ:{}:_AVERAGE".format(axis), wait=full_averaging_time + 5
            )

            # Check the final value is correct
            self.ca.process_pv("TAKEDATA")
            self.ca.assert_that_pv_is_number(pv, field_number)
