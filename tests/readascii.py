import os
import unittest
import shutil
from contextlib import contextmanager

from utils.channel_access import ChannelAccess


DEFAULT_SETTINGS_DIR = \
    os.path.join("C:/", "Instrument", "Apps", "EPICS", "support", "ReadASCII", "master", "example_settings")
DEFAULT_SETTINGS_FILE = "Default.txt"

TEMP_TEST_SETTINGS_DIR = os.path.join("C:/", "Instrument", "var", "tmp", "readascii_test")
TEMP_SETTINGS_FILE_NAME = "test_temp.txt"


# Tolerance for floating-point readback values
TOLERANCE = 10**-5


class ReadasciiTests(unittest.TestCase):
    """
    Tests for ReadASCII
    """
    @contextmanager
    def generate_temporary_test_file(self, data):
        """
        Context manager which generates a temporary test file containing the given data.
        :param data: a list of 5-element tuples (setpoint, p, i, d, heater_range)
        """
        if not os.path.exists(TEMP_TEST_SETTINGS_DIR):
            os.mkdir(TEMP_TEST_SETTINGS_DIR)

        try:
            with open(os.path.join(TEMP_TEST_SETTINGS_DIR, TEMP_SETTINGS_FILE_NAME), "w") as f:
                f.write("SP P I D HEATER\n")
                for row in data:
                    assert len(row) == 5, "Each row should have exactly 5 elements"
                    f.write("{}\n".format(" ".join(str(d) for d in row)))

            yield
        finally:
            shutil.rmtree(TEMP_TEST_SETTINGS_DIR)

    @contextmanager
    def use_test_file(self):
        """
        Context manager which sets the ReadASCII file to the temporary test file on entry, and reverts it back to the
        default on exit.
        """
        def _set_and_use_file(dir, name):
            self.ca.assert_setting_setpoint_sets_readback(dir, "DIRBASE")
            self.ca.assert_setting_setpoint_sets_readback(name, "RAMP_FILE")
            self.ca.set_pv_value("LUTON", 1)

        try:
            _set_and_use_file(TEMP_TEST_SETTINGS_DIR, TEMP_SETTINGS_FILE_NAME)
            yield
        finally:
            _set_and_use_file(DEFAULT_SETTINGS_DIR, DEFAULT_SETTINGS_FILE)

    def _set_and_check(self, current_val, p, i, d, output_range):
        self.ca.set_pv_value("CURRENT_VAL", current_val)

        # The LUTON PV is FLNK'ed to by the IOCs that use ReadASCII after the setpoint changes.
        # Here we're not using any particular IOC so have to trigger the processing manually.
        self.ca.set_pv_value("LUTON.PROC", 1)

        self.ca.assert_that_pv_is_number("OUT_P", p, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_I", i, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_D", d, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_MAX", output_range, tolerance=TOLERANCE)

    def setUp(self):
        self.ca = ChannelAccess(default_timeout=30, device_prefix="READASCIITEST")
        self.ca.wait_for("DIRBASE")

    def test_GIVEN_the_test_file_has_entries_for_a_setpoint_WHEN_that_exact_setpoint_is_set_THEN_it_updates_the_pid_pvs_with_the_values_from_the_file(self):
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        with self.generate_temporary_test_file(rows), self.use_test_file():
            for row in rows:
                self._set_and_check(*row)

    def test_GIVEN_the_test_file_has_non_integer_pid_entries_for_a_setpoint_WHEN_that_exact_setpoint_is_set_THEN_it_updates_the_pid_pvs_with_the_values_from_the_file(self):
        rows = [
            (50, 1.23, 2.7, 3.8, 4.1),
            (100, 5.555, 6.666, 7.777, 8.888),
            (150, 9.1, 10.2, 11.3, 12.4),
        ]

        with self.generate_temporary_test_file(rows), self.use_test_file():
            for row in rows:
                self._set_and_check(*row)

    def test_WHEN_a_setpoint_lower_than_the_minimum_bound_of_the_file_is_set_THEN_the_pid_settings_are_updated_to_be_the_minimum(self):
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
        ]

        with self.generate_temporary_test_file(rows), self.use_test_file():
            self._set_and_check(20, 1, 2, 3, 4)
            self._set_and_check(120, 5, 6, 7, 8)
            self._set_and_check(20, 1, 2, 3, 4)
