import os
import unittest
import shutil

import time

from utils.channel_access import ChannelAccess


DEFAULT_SETTINGS_DIR = \
    os.path.join("C:/", "Instrument", "Apps", "EPICS", "support", "ReadASCII", "master", "example_settings")

TEMP_TEST_SETTINGS_DIR = os.path.join("C:/", "Instrument", "var", "tmp", "readascii_test")

DEFAULT_SETTINGS_FILE = "Default.txt"


def _generate_test_file_name():
    """
    :return: an available filename in TEMP_TEST_SETTINGS_DIR
    """
    i = 1
    while True:
        filename = "test_file_{}.txt".format(i)
        filepath = os.path.join(TEMP_TEST_SETTINGS_DIR, filename)
        if not os.path.exists(filepath):
            return filename
        i += 1


def _generate_test_file(data=((1, 1, 1, 1, 1),)):
    """
    Generates a test file populated with the data given
    :param data: A collection of 5-element tuples containing the data to go into the file
    :return: The name of the generated file
    """
    name = _generate_test_file_name()
    with open(os.path.join(TEMP_TEST_SETTINGS_DIR, name), "w") as f:
        f.write("SP P I D HEATER\n")

        for row in data:
            if len(row) != 5:
                raise ValueError("Each row should have exactly 5 elements")

            f.write("{}\n".format(" ".join(str(d) for d in row)))

    return name


def _generate_new_directory_containing_default_settings():
    """
    Generates a new directory in TEMP_TEST_SETTINGS_DIR, containing a
    Default.txt settings file copied from DEFAULT_SETTINGS_DIR
    :return: the name of the created directory
    """
    i = 1
    while True:
        dirname = "test_dir_{}".format(i)
        dirpath = os.path.join(TEMP_TEST_SETTINGS_DIR, dirname)

        if not os.path.exists(dirpath):
            os.mkdir(dirpath)

        if not os.path.exists(os.path.join(dirpath, DEFAULT_SETTINGS_FILE)):

            shutil.copyfile(os.path.join(DEFAULT_SETTINGS_DIR, DEFAULT_SETTINGS_FILE),
                            os.path.join(dirpath, DEFAULT_SETTINGS_FILE))

            return dirpath
        i += 1


class ReadasciiTests(unittest.TestCase):
    """
    Tests for ReadASCII
    """

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEMP_TEST_SETTINGS_DIR):
            shutil.rmtree(TEMP_TEST_SETTINGS_DIR)

        try:
            os.mkdir(TEMP_TEST_SETTINGS_DIR)
        except OSError:
            # Sometimes the file is still marked as "in use" but is no longer in use after a short wait.
            time.sleep(1)
            os.mkdir(TEMP_TEST_SETTINGS_DIR)

        shutil.copyfile(os.path.join(DEFAULT_SETTINGS_DIR, DEFAULT_SETTINGS_FILE),
                        os.path.join(TEMP_TEST_SETTINGS_DIR, DEFAULT_SETTINGS_FILE))

    def setUp(self):
        self.ca = ChannelAccess(default_timeout=30, device_prefix="READASCIITEST")
        self.ca.wait_for("DIRBASE")

        # Reset directory to the default in case one of the tests changed it
        self._reset_file_location()

    def _reset_file_location(self):
        self.assertTrue(os.path.isdir(TEMP_TEST_SETTINGS_DIR))
        self.assertTrue(os.path.exists(os.path.join(TEMP_TEST_SETTINGS_DIR, DEFAULT_SETTINGS_FILE)))

        self.ca.assert_setting_setpoint_sets_readback(TEMP_TEST_SETTINGS_DIR, "DIRBASE")
        self.ca.assert_setting_setpoint_sets_readback(DEFAULT_SETTINGS_FILE, "RAMP_FILE")

    def test_WHEN_base_dir_is_set_THEN_base_dir_readback_gives_value_just_set(self):
        path = _generate_new_directory_containing_default_settings()
        self.ca.assert_setting_setpoint_sets_readback(path, "DIRBASE")

    def test_GIVEN_file_exists_WHEN_ramp_file_is_set_THEN_ramp_file_readback_contains_file_just_set(self):
        filename = _generate_test_file()
        self.ca.assert_setting_setpoint_sets_readback(filename, "RAMP_FILE")

    def _set_and_check(self, current_val, p, i, d, output_range):
        self.ca.set_pv_value("CURRENT_VAL", current_val)

        # The LUTON PV is FLNK'ed to by the IOCs that use ReadASCII after the setpoint changes.
        # Here we're not using any particular IOC so have to trigger the processing manually.
        self.ca.set_pv_value("LUTON.PROC", 1)

        self.ca.assert_that_pv_is("OUT_P", p)
        self.ca.assert_that_pv_is("OUT_I", i)
        self.ca.assert_that_pv_is("OUT_D", d)
        self.ca.assert_that_pv_is("OUT_MAX", output_range)

    def test_GIVEN_the_test_file_has_entries_for_a_setpoint_WHEN_that_exact_setpoint_is_set_THEN_it_updates_the_pid_pvs_with_the_values_from_the_file(self):
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
            (150, 9, 10, 11, 12),
        ]

        filename = _generate_test_file(rows)
        self.ca.assert_setting_setpoint_sets_readback(filename, "RAMP_FILE")
        self.ca.set_pv_value("LUTON", 1)

        for row in rows:
            self._set_and_check(*row)

    def test_WHEN_a_setpoint_lower_than_the_minimum_bound_of_the_file_is_set_THEN_the_pid_settings_are_updated_to_be_the_minimum(self):
        rows = [
            (50, 1, 2, 3, 4),
            (100, 5, 6, 7, 8),
        ]

        filename = _generate_test_file(rows)
        self.ca.assert_setting_setpoint_sets_readback(filename, "RAMP_FILE")
        self.ca.set_pv_value("LUTON", 1)

        self._set_and_check(20, 1, 2, 3, 4)
        self._set_and_check(120, 5, 6, 7, 8)
        self._set_and_check(20, 1, 2, 3, 4)
