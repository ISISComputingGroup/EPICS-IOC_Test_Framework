import os
import unittest
import shutil
import time
from contextlib import contextmanager

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP
from utils.test_modes import TestModes
from utils.ioc_launcher import IOCRegister
from parameterized import parameterized

DEFAULT_SETTINGS_DIR = \
    os.path.join("C:/", "Instrument", "Apps", "EPICS", "support", "ReadASCII", "master", "example_settings")
DEFAULT_SETTINGS_FILE = "Default.txt"

TEMP_TEST_SETTINGS_DIR = os.path.join("C:/", "Instrument", "var", "tmp", "readascii_test")
TEMP_SETTINGS_FILE_NAME = "test_temp.txt"

# Tolerance for floating-point readback values
TOLERANCE = 10 ** -5

DEVICE_PREFIX = "READASCIITEST"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "support", "ReadASCII", "master", "iocBoot", "iocReadASCIITest"),
        "pv_for_existence": "DIRBASE",
    },
]

TEST_MODES = [TestModes.RECSIM]

SECONDS_PER_MINUTE = 60

TEST_VALUES = [
    0.123456789,
    987654321,
]


class ReadasciiTests(unittest.TestCase):
    """
    Tests for ReadASCII
    """

    def _write_contents_of_temporary_test_file(self, headers, data, name=TEMP_SETTINGS_FILE_NAME):
        """
        Writes the given data to the temporary test file.

        This method assumes that the test directory exists (e.g. it has been created by _generate_temporary_test_file)

        :param data: a list of 5-element tuples (setpoint, p, i, d, heater_range)
        """
        with open(os.path.join(TEMP_TEST_SETTINGS_DIR, name), "w") as f:
            f.write("{}\n".format(" ".join(str(d) for d in headers)))
            for row in data:
                f.write("{}\n".format(" ".join(str(d) for d in row)))
        time.sleep(5)  # allow new file on disk to be noticed

    @contextmanager
    def _generate_temporary_test_file(self, headers, data, name=TEMP_SETTINGS_FILE_NAME):
        """
        Context manager which generates a temporary test file containing the given data.
        :param data: a list of 5-element tuples (setpoint, p, i, d, heater_range)
        """
        if not os.path.exists(TEMP_TEST_SETTINGS_DIR):
            os.mkdir(TEMP_TEST_SETTINGS_DIR)

        try:
            self._write_contents_of_temporary_test_file(headers, data, name)
            yield
        finally:
            shutil.rmtree(TEMP_TEST_SETTINGS_DIR)

    def _set_and_use_file(self, directory, name):
        self.ca.assert_setting_setpoint_sets_readback(directory, "DIRBASE")
        self.ca.assert_setting_setpoint_sets_readback(name, "RAMP_FILE")
        self.ca.set_pv_value("LUTON", 1)

    @contextmanager
    def _use_test_file(self, name=TEMP_SETTINGS_FILE_NAME):
        """
        Context manager which sets the ReadASCII file to the temporary test file on entry, and reverts it back to the
        default on exit.

        Need to set the file back to the default one on exit, otherwise the file will be marked as "in use" and
        cannot be deleted properly
        """
        try:
            self._set_and_use_file(TEMP_TEST_SETTINGS_DIR, name)
            yield
        finally:
            self._set_and_use_file(DEFAULT_SETTINGS_DIR, DEFAULT_SETTINGS_FILE)

    def _set_and_check(self, current_val, p, i, d, output_range):
        self.ca.set_pv_value("CURRENT_VAL", current_val)

        # The LUTON PV is FLNK'ed to by the IOCs that use ReadASCII after the setpoint changes.
        # Here we're not using any particular IOC so have to trigger the processing manually.
        self.ca.assert_that_pv_is("LUTON:RBV", "1")
        self.ca.assert_that_pv_is("LUTON", "1")
        self.ca.process_pv("LUTON")

        self.ca.assert_that_pv_is_number("OUT_P", p, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_I", i, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_D", d, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_MAX", output_range, tolerance=TOLERANCE)

    def _set_and_check_flexible(self, current_val, pv_names, pv_values):
        self.ca.set_pv_value("CURRENT_VAL", current_val)

        # The LUTON PV is FLNK'ed to by the IOCs that use ReadASCII after the setpoint changes.
        # Here we're not using any particular IOC so have to trigger the processing manually.
        self.ca.assert_that_pv_is("LUTON:RBV", "1")
        self.ca.assert_that_pv_is("LUTON", "1")
        self.ca.process_pv("LUTON")

        for i in range(len(pv_names)):
            self.ca.assert_that_pv_is_number(str(pv_names[i]), float(pv_values[i]), tolerance=TOLERANCE)

    def setUp(self):
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DIRBASE")
        self._set_ramp_status(False)

    def _set_ramp_status(self, status):
        self.ca.set_pv_value("RAMPON", status)

    @parameterized.expand([
        ("new MH header name", "MH"),
        ("old MH header name", "heater"),
    ])
    def test_GIVEN_the_test_file_has_entries_for_a_setpoint_WHEN_that_exact_setpoint_is_set_THEN_it_updates_the_pid_pvs_with_the_values_from_the_file(
            self, _, MH_name):
        headers = ["SP", "P", "I", "D", MH_name]
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check(*row)

    def test_GIVEN_the_test_file_has_non_integer_pid_entries_for_a_setpoint_WHEN_that_exact_setpoint_is_set_THEN_it_updates_the_pid_pvs_with_the_values_from_the_file(
            self):
        headers = ["SP", "P", "I", "D", "MH"]
        rows = [
            (50, 1.23, 2.7, 3.8, 4.1),
            (100, 5.555, 6.666, 7.777, 8.888),
            (150, 9.1, 10.2, 11.3, 12.4),
        ]

        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check(*row)

    def test_WHEN_a_setpoint_lower_than_the_minimum_bound_of_the_file_is_set_THEN_the_pid_settings_are_updated_to_be_the_minimum(
            self):
        headers = ["SP", "P", "I", "D", "MH"]
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
        ]

        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            self._set_and_check(20, 1, 2, 3, 4)
            self._set_and_check(120, 5, 6, 7, 8)
            self._set_and_check(20, 1, 2, 3, 4)

    def test_GIVEN_the_test_file_has_entries_for_a_setpoint_WHEN_the_file_is_changed_on_disk_THEN_the_pid_lookup_uses_the_new_values(
            self):
        headers = ["SP", "P", "I", "D", "MH"]
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check(*row)

            new_rows = [[item + 10 for item in row] for row in rows]
            self._write_contents_of_temporary_test_file(headers, new_rows)
            self.assertNotEqual(rows, new_rows)

            for row in new_rows:
                self._set_and_check(*row)

    def test_GIVEN_ramping_is_off_WHEN_setting_setpoint_THEN_it_is_sent_to_device_immediately(self):
        self._set_ramp_status(False)
        for val in TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(val, set_point_pv="VAL:SP", readback_pv="OUT_SP")

    def test_GIVEN_ramping_is_on_WHEN_setting_setpoint_THEN_setpoint_sent_to_the_device_ramps(self):
        # This ensures that other tests don't mess with this one
        headers = ["SP", "P", "I", "D", "MH"]
        rows = [(0, 0, 0, 0, 0), ]
        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            pass

        setpoint_change = 1  # K

        # secs - The test will take at least this long to run but if it's too small may get random timing problems
        # causing the test to fail
        ramp_time = 20

        ramp_rate = setpoint_change * SECONDS_PER_MINUTE / ramp_time  # K per min

        # Ensure ramp is off and setpoint is zero initially
        self._set_ramp_status(False)
        self.ca.set_pv_value("VAL:SP", 0)
        self.ca.assert_that_pv_is("OUT_SP", 0)

        self.ca.set_pv_value("CURRENT_VAL", 0)
        self.ca.assert_that_pv_is("CURRENT_VAL", 0)

        # Set up ramp and set a setpoint so that the ramp starts.
        self.ca.assert_setting_setpoint_sets_readback(ramp_rate, "RATE")
        self._set_ramp_status(True)
        self.ca.set_pv_value("VAL:SP", setpoint_change, wait=True)

        # Verify that setpoint does not reach final value within first half of ramp time
        self.ca.assert_that_pv_is_not("OUT_SP", setpoint_change, timeout=ramp_time / 2)

        # ... But after a further ramp_time, it should have.
        # We give it another 3 seconds here in case it hasn't finished ramping.
        self.ca.assert_that_pv_is("OUT_SP", setpoint_change, timeout=ramp_time + 3)

    def test_GIVEN_the_test_file_has_not_enough_columns_THEN_it_updates_only_known_columns(self):
        headers = ["SP", "P", "I", "D", "MH"]
        # we are expecting all the values to be normal
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        headers2 = ["SP", "P", "I", "D"]
        # since we don't have MH, we expect 12 to be output to OUT:MAX on any set point since it was last set value
        rows2 = [
            (50, 1, 2, 3),
            (100, 5, 6, 7),
            (150, 9, 10, 11),
        ]

        check_pvs = ["OUT_P", "OUT_I", "OUT_D", "OUT_MAX"]
        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:])
            self._write_contents_of_temporary_test_file(headers2, rows2)
            for row in rows2:
                self._set_and_check_flexible(row[0], check_pvs, row[1:] + (12,))

    def test_GIVEN_the_test_file_has_too_many_columns_THEN_it_updates_only_known_columns(self):
        headers = ["SP", "P", "I", "D", "MH", "UNKNOWN"]
        # we are expecting all the values to be normal
        rows = [
            (50, 1, 2, 3, 4, 13),
            (100, 5, 6, 7, 8, 14),
            (150, 9, 10, 11, 12, 15),
        ]

        check_pvs = ["OUT_P", "OUT_I", "OUT_D", "OUT_MAX"]
        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:5])

    def test_WHEN_the_test_file_header_is_lost_THEN_last_column_values_remain(self):
        headers = ["SP", "P", "I", "D", "MH"]
        # we are expecting all the values to be normal
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        headers2 = ["SP", "P", "I", "UNKNOWN", "MH"]
        # we are expecting last value where D would be normally. Last value is going to be 11
        # since it's last in the table to set-and-check

        check_pvs = ["OUT_P", "OUT_I", "OUT_D", "OUT_MAX"]
        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:])
            self._write_contents_of_temporary_test_file(headers2, rows)
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:3] + (11,) + row[4:])

    def test_GIVEN_the_test_file_incorrectly_formatted_THEN_interpret_existing_data_without_failing(self):
        headers = ["SP", "P", "I", "D", "MH"]
        # we are missing value for MH between 100-150 so it should instead parse data below (12)
        # for value above 150 it should then give 0 as there is no record to parse
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7),
            (150, 9, 10, 11, 12),
        ]

        rows_expected = [
            (1, 2, 3, 4),
            (5, 6, 7, 12),
            (9, 10, 11, 0),
        ]

        check_pvs = ["OUT_P", "OUT_I", "OUT_D", "OUT_MAX"]
        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for i in range(len(rows)):
                self._set_and_check_flexible(rows[i][0], check_pvs, rows_expected[i])

    def test_GIVEN_the_test_file_has_column_repeated_THEN_last_column_overwrite(self):
        headers = ["SP", "P", "I", "D", "MH", "D"]
        # we are expecting all the values to be normal
        rows = [
            (50, 1, 2, 3, 4, 13),
            (100, 5, 6, 7, 8, 14),
            (150, 9, 10, 11, 12, 15),
        ]

        check_pvs = ["OUT_P", "OUT_I", "OUT_MAX", "OUT_D"]
        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:3]+row[4:])

    def test_GIVEN_data_file_name_changed_THEN_new_file_used(self):
        headers = ["SP", "P", "I", "D", "MH"]
        # we are expecting all the values to be normal
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        check_pvs = ["OUT_P", "OUT_I", "OUT_D", "OUT_MAX"]
        with self._generate_temporary_test_file(headers, rows), self._use_test_file():
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:])

        headers = ["SP", "P", "I", "D", "MH"]
        # we are expecting all the values to be normal again but loaded from different file
        rows = [
            (100, 10, 20, 30, 40),
            (200, 50, 60, 70, 80),
            (300, 90, 95, 97, 99),
        ]

        check_pvs = ["OUT_P", "OUT_I", "OUT_D", "OUT_MAX"]
        # we use file2 this time and expect new values
        with self._generate_temporary_test_file(headers, rows, "file2"), self._use_test_file("file2"):
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:])

    def test_GIVEN_invalid_filename_then_fixing_it_THEN_first_alarm_then_correct(self):
        # this should put file pv on alarm since we set a non-existing file
        self.ca.assert_setting_setpoint_sets_readback(TEMP_TEST_SETTINGS_DIR, "DIRBASE")
        self.ca.set_pv_value("RAMP_FILE", "FakeFile")
        self.ca.assert_setting_setpoint_sets_readback("FakeFile", "RAMP_FILE", None, None, "INVALID")

        headers = ["SP", "P", "I", "D", "MH"]
        # we are expecting all the values to be normal when using real file
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        check_pvs = ["OUT_P", "OUT_I", "OUT_D", "OUT_MAX"]
        with self._generate_temporary_test_file(headers, rows, "RealFile"), self._use_test_file("RealFile"):
            for row in rows:
                self._set_and_check_flexible(row[0], check_pvs, row[1:])
    

    def test_GIVEN_no_file_is_set_THEN_file_changed_PV_is_false(self):
        self.ca.set_pv_value("RAMP_FILE", DEFAULT_SETTINGS_FILE)
        self.ca.assert_that_pv_is("RAMP_FILE_CHANGED", 0)

    def test_GIVEN_file_is_set_THEN__file_changed_PV_is_true(self):
        headers = ["SP", "P", "I", "D", "MH"]
        rows = [(0, 0, 0, 0, 0), ]

        with self._generate_temporary_test_file(headers, rows, "RealFile"), self._use_test_file("RealFile"):
            self.ca.assert_that_pv_is("RAMP_FILE_CHANGED", 1)

