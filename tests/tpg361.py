import unittest

from common_tests.tpgx6x import TpgBase, ErrorFlags, ErrorStrings
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from parameterized import parameterized


DEVICE_PREFIX = "TPG36X_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TPG36X"),
        "emulator": "tpgx6x",
        "lewis_protocol": "tpg361",
        "macros": {
            "IS361": "Y"
        }
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tpg361Tests(TpgBase, unittest.TestCase):
    def get_prefix(self):
        return DEVICE_PREFIX

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_set_WHEN_read_THEN_pressure_is_as_expected(self, _, channel):
        if channel == 1:
            expected_pressure = 1.23
            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is("{}:PRESSURE".format(channel), expected_pressure)
            self.ca.assert_that_pv_alarm_is("{}:PRESSURE".format(channel), self.ca.Alarms.NONE)
            self.ca.assert_that_pv_is("{}:ERROR".format(channel), "No Error")

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_negative_pressure_set_WHEN_read_THEN_pressure_is_as_expected(self, _, channel):
        if channel == 1:
            expected_pressure = -123.34
            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is("{}:PRESSURE".format(channel), expected_pressure)

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_with_no_decimal_places_set_WHEN_read_THEN_pressure_is_as_expected(self, _, channel):
        if channel == 1:
            expected_pressure = 7
            self._set_pressure(expected_pressure, channel)

            self.ca.assert_that_pv_is("{}:PRESSURE".format(channel), expected_pressure)

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_under_range_set_WHEN_read_THEN_error(self, _, channel):
        if channel == 1:
            expected_error = ErrorFlags.UNDER_RANGE
            expected_error_str = ErrorStrings.UNDER_RANGE
            expected_alarm = self.ca.Alarms.MINOR
            self._set_error(expected_error, channel)

            self.ca.assert_that_pv_is("{}:ERROR".format(channel), expected_error_str)
            self.ca.assert_that_pv_alarm_is("{}:ERROR".format(channel), expected_alarm)

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_over_range_set_WHEN_read_THEN_error(self, _, channel):
        if channel == 1:
            expected_error = ErrorFlags.OVER_RANGE
            expected_error_str = ErrorStrings.OVER_RANGE
            expected_alarm = self.ca.Alarms.MINOR
            self._set_error(expected_error, channel)

            self.ca.assert_that_pv_is("{}:ERROR".format(channel), expected_error_str)
            self.ca.assert_that_pv_alarm_is("{}:ERROR".format(channel), expected_alarm)

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_sensor_error_set_WHEN_read_THEN_error(self, _, channel):
        if channel == 1:
            expected_error = ErrorFlags.SENSOR_ERROR
            expected_error_str = ErrorStrings.SENSOR_ERROR
            expected_alarm = self.ca.Alarms.MAJOR
            self._set_error(expected_error, channel)

            self.ca.assert_that_pv_is("{}:ERROR".format(channel), expected_error_str)
            self.ca.assert_that_pv_alarm_is("{}:ERROR".format(channel), expected_alarm)

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_sensor_off_set_WHEN_read_THEN_error(self, _, channel):
        if channel == 1:
            expected_error = ErrorFlags.SENSOR_OFF
            expected_error_str = ErrorStrings.SENSOR_OFF
            expected_alarm = self.ca.Alarms.MAJOR
            self._set_error(expected_error, channel)

            self.ca.assert_that_pv_is("{}:ERROR".format(channel), expected_error_str)
            self.ca.assert_that_pv_alarm_is("{}:ERROR".format(channel), expected_alarm)

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_no_sensor_set_WHEN_read_THEN_error(self, _, channel):
        if channel == 1:
            expected_error = ErrorFlags.NO_SENSOR
            expected_error_str = ErrorStrings.NO_SENSOR
            expected_alarm = self.ca.Alarms.MAJOR
            self._set_error(expected_error, channel)

            self.ca.assert_that_pv_is("{}:ERROR".format(channel), expected_error_str)
            self.ca.assert_that_pv_alarm_is("{}:ERROR".format(channel), expected_alarm)

    @parameterized.expand(("Pressure_{}".format(i), i) for i in range(1, 3))
    def test_GIVEN_pressure_identification_error_set_WHEN_read_THEN_error(self, _, channel):
        if channel == 1:
            expected_error = ErrorFlags.IDENTIFICATION_ERROR
            expected_error_str = ErrorStrings.IDENTIFICATION_ERROR
            expected_alarm = self.ca.Alarms.MAJOR
            self._set_error(expected_error, channel)

            self.ca.assert_that_pv_is("{}:ERROR".format(channel), expected_error_str)
            self.ca.assert_that_pv_alarm_is("{}:ERROR".format(channel), expected_alarm)
