from __future__ import division

import os
import unittest
import shutil
from contextlib import contextmanager

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP
from utils.test_modes import TestModes
from utils.ioc_launcher import IOCRegister

DEFAULT_SETTINGS_DIR = \
    os.path.join("C:/", "Instrument", "Apps", "EPICS", "support", "ReadASCII", "master", "example_settings")
DEFAULT_SETTINGS_FILE = "Default.txt"

TEMP_TEST_SETTINGS_DIR = os.path.join("C:/", "Instrument", "var", "tmp", "readascii_test")
TEMP_SETTINGS_FILE_NAME = "test_temp.txt"


# Tolerance for floating-point readback values
TOLERANCE = 10**-5

DEVICE_PREFIX = "READASCIITEST"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "support", "ReadASCII", "master", "iocBoot", "iocReadASCIITest"),
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
    def _write_contents_of_temporary_test_file(self, data):
        """
        Writes the given data to the temporary test file.

        This method assumes that the test directory exists (e.g. it has been created by _generate_temporary_test_file)

        :param data: a list of 5-element tuples (setpoint, p, i, d, heater_range)
        """
        with open(os.path.join(TEMP_TEST_SETTINGS_DIR, TEMP_SETTINGS_FILE_NAME), "w") as f:
            f.write("SP P I D HEATER\n")
            for row in data:
                assert len(row) == 5, "Each row should have exactly 5 elements"
                f.write("{}\n".format(" ".join(str(d) for d in row)))

    @contextmanager
    def _generate_temporary_test_file(self, data):
        """
        Context manager which generates a temporary test file containing the given data.
        :param data: a list of 5-element tuples (setpoint, p, i, d, heater_range)
        """
        if not os.path.exists(TEMP_TEST_SETTINGS_DIR):
            os.mkdir(TEMP_TEST_SETTINGS_DIR)

        try:
            self._write_contents_of_temporary_test_file(data)
            yield
        finally:
            shutil.rmtree(TEMP_TEST_SETTINGS_DIR)

    def _set_and_use_file(self, dir, name):
        self.ca.assert_setting_setpoint_sets_readback(dir, "DIRBASE")
        self.ca.assert_setting_setpoint_sets_readback(name, "RAMP_FILE")
        self.ca.set_pv_value("LUTON", 1)

    @contextmanager
    def _use_test_file(self):
        """
        Context manager which sets the ReadASCII file to the temporary test file on entry, and reverts it back to the
        default on exit.

        Need to set the file back to the default one on exit, otherwise the file will be marked as "in use" and
        cannot be deleted properly
        """
        try:
            self._set_and_use_file(TEMP_TEST_SETTINGS_DIR, TEMP_SETTINGS_FILE_NAME)
            yield
        finally:
            self._set_and_use_file(DEFAULT_SETTINGS_DIR, DEFAULT_SETTINGS_FILE)

    def _set_and_check(self, current_val, p, i, d, output_range):
        self.ca.set_pv_value("CURRENT_VAL", current_val)

        # The LUTON PV is FLNK'ed to by the IOCs that use ReadASCII after the setpoint changes.
        # Here we're not using any particular IOC so have to trigger the processing manually.
        self.ca.process_pv("LUTON")

        self.ca.assert_that_pv_is_number("OUT_P", p, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_I", i, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_D", d, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("OUT_MAX", output_range, tolerance=TOLERANCE)

    def setUp(self):
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca.wait_for("DIRBASE")
        self._set_ramp_status(False)

    def test_GIVEN_the_test_file_has_entries_for_a_setpoint_WHEN_that_exact_setpoint_is_set_THEN_it_updates_the_pid_pvs_with_the_values_from_the_file(self):
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        with self._generate_temporary_test_file(rows), self._use_test_file():
            for row in rows:
                self._set_and_check(*row)

    def test_GIVEN_the_test_file_has_non_integer_pid_entries_for_a_setpoint_WHEN_that_exact_setpoint_is_set_THEN_it_updates_the_pid_pvs_with_the_values_from_the_file(self):
        rows = [
            (50, 1.23, 2.7, 3.8, 4.1),
            (100, 5.555, 6.666, 7.777, 8.888),
            (150, 9.1, 10.2, 11.3, 12.4),
        ]

        with self._generate_temporary_test_file(rows), self._use_test_file():
            for row in rows:
                self._set_and_check(*row)

    def test_WHEN_a_setpoint_lower_than_the_minimum_bound_of_the_file_is_set_THEN_the_pid_settings_are_updated_to_be_the_minimum(self):
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
        ]

        with self._generate_temporary_test_file(rows), self._use_test_file():
            self._set_and_check(20, 1, 2, 3, 4)
            self._set_and_check(120, 5, 6, 7, 8)
            self._set_and_check(20, 1, 2, 3, 4)

    def test_GIVEN_the_test_file_has_entries_for_a_setpoint_WHEN_the_file_is_changed_on_disk_THEN_the_pid_lookup_uses_the_new_values(self):
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        with self._generate_temporary_test_file(rows), self._use_test_file():
            for row in rows:
                self._set_and_check(*row)

            new_rows = [[item+10 for item in row] for row in rows]
            self._write_contents_of_temporary_test_file(new_rows)
            self.assertNotEqual(rows, new_rows)

            for row in new_rows:
                self._set_and_check(*row)

    def _set_ramp_status(self, status):
        self.ca.set_pv_value("RAMPON", status)

    def test_GIVEN_ramping_is_off_WHEN_setting_setpoint_THEN_it_is_sent_to_device_immediately(self):
        self._set_ramp_status(False)
        for val in TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(val, set_point_pv="VAL:SP", readback_pv="OUT_SP")

    def test_GIVEN_ramping_is_on_WHEN_setting_setpoint_THEN_setpoint_sent_to_the_device_ramps(self):
        setpoint_change = 1  # K

        # secs - The test will take at least this long to run but if it's too small may get random timing problems
        # causing the test to fail
        ramp_time = 20

        ramp_rate = setpoint_change * SECONDS_PER_MINUTE / ramp_time  # K per min

        # Ensure ramp is off and setpoint is zero initially
        self._set_ramp_status(False)
        self.ca.set_pv_value("VAL:SP", 0)
        self.ca.assert_that_pv_is("OUT_SP", 0)

        # Set up ramp and set a setpoint so that the ramp starts.
        self.ca.assert_setting_setpoint_sets_readback(ramp_rate, "RATE")
        self._set_ramp_status(True)
        self.ca.set_pv_value("VAL:SP", setpoint_change)

        # Verify that setpoint does not reach final value within first half of ramp time
        self.ca.assert_that_pv_is_not("OUT_SP", setpoint_change, timeout=ramp_time/2)

        # ... But after a further ramp_time, it should have.
        self.ca.assert_that_pv_is("OUT_SP", setpoint_change, timeout=ramp_time)
