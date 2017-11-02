import unittest
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc

# MACROS to use for the IOC
MACROS = {}


class UnitFlags(object):
    MBAR = 0
    TORR = 1
    PA = 2


class UnitStrings(object):
    MBAR = "mbar"
    TORR = "Torr"
    PA = "Pa"


class ErrorFlags(object):
    NO_ERROR = 0
    UNDER_RANGE = 1
    OVER_RANGE = 2
    SENSOR_ERROR = 3
    SENSOR_OFF = 4
    NO_SENSOR = 5
    IDENTIFICATION_ERROR = 6


class ErrorStrings(object):
    NO_ERROR = "No Error"
    UNDER_RANGE = "Underrange"
    OVER_RANGE = "Overrange"
    SENSOR_ERROR = "Sensor error"
    SENSOR_OFF = "Sensor off"
    NO_SENSOR = "No Sensor"
    IDENTIFICATION_ERROR = "Identification Error"


class Tpg26xTests(unittest.TestCase):
    """
    Tests for the TPG26x.
    """

    CHANNEL_ONE = 1
    CHANNEL_TWO = 2

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tpg26x")

        self.ca = ChannelAccess(device_prefix="TPG26X_01")
        self.ca.wait_for("1:PRESSURE")
        # Reset and error flags and alarms
        self._set_error(ErrorStrings.NO_ERROR, self.CHANNEL_ONE)
        self._set_error(ErrorStrings.NO_ERROR, self.CHANNEL_TWO)

    def _set_pressure(self, expected_pressure, channel):
        pv = "SIM:{0:d}:PRESSURE".format(channel)
        prop = "pressure{0:d}".format(channel)
        self._lewis.backdoor_set_on_device(prop, expected_pressure)
        self._ioc.set_simulated_value(pv, expected_pressure)

    def _set_error(self, expected_error, channel):
        pv = "SIM:{0:d}:ERROR".format(channel)
        prop = "error{0:d}".format(channel)
        self._lewis.backdoor_set_on_device(prop, expected_error)
        self._ioc.set_simulated_value(pv, expected_error)

    def _set_units(self, expected_units):
        self._lewis.backdoor_set_on_device("units", expected_units)
        self._ioc.set_simulated_value("SIM:UNITS", expected_units)

    def test_GIVEN_pressure1_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:PRESSURE", expected_pressure)
        self.ca.assert_pv_alarm_is("1:PRESSURE", ChannelAccess.ALARM_NONE)
        self.ca.assert_that_pv_is("1:ERROR", "No Error")

    def test_GIVEN_negative_pressure1_set_WHEN_read_THEN_pressure1_is_as_expected(self):
        expected_pressure = -123.34
        self._set_pressure(expected_pressure, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:PRESSURE", expected_pressure)

    def test_GIVEN_pressure1_with_no_decimal_places_set_WHEN_read_THEN_pressure1_is_as_expected(self):
        expected_pressure = 7
        self._set_pressure(expected_pressure, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:PRESSURE", expected_pressure)

    def test_GIVEN_pressure1_under_range_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.UNDER_RANGE
        expected_error_str = ErrorStrings.UNDER_RANGE
        expected_alarm = ChannelAccess.ALARM_MINOR
        self._set_error(expected_error, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("1:ERROR", expected_alarm)

    def test_GIVEN_pressure1_over_range_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.OVER_RANGE
        expected_error_str = ErrorStrings.OVER_RANGE
        expected_alarm = ChannelAccess.ALARM_MINOR
        self._set_error(expected_error, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("1:ERROR", expected_alarm)

    def test_GIVEN_pressure1_sensor_error_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.SENSOR_ERROR
        expected_error_str = ErrorStrings.SENSOR_ERROR
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("1:ERROR", expected_alarm)

    def test_GIVEN_pressure1_sensor_off_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.SENSOR_OFF
        expected_error_str = ErrorStrings.SENSOR_OFF
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("1:ERROR", expected_alarm)

    def test_GIVEN_pressure1_no_sensor_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.NO_SENSOR
        expected_error_str = ErrorStrings.NO_SENSOR
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("1:ERROR", expected_alarm)

    def test_GIVEN_pressure1_identification_error_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.IDENTIFICATION_ERROR
        expected_error_str = ErrorStrings.IDENTIFICATION_ERROR
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("1:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("1:ERROR", expected_alarm)

    def test_GIVEN_pressure2_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:PRESSURE", expected_pressure)
        self.ca.assert_pv_alarm_is("2:PRESSURE", ChannelAccess.ALARM_NONE)
        self.ca.assert_that_pv_is("2:ERROR", "No Error")

    def test_GIVEN_negative_pressure2_set_WHEN_read_THEN_pressure2_is_as_expected(self):
        expected_pressure = -123.34
        self._set_pressure(expected_pressure, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:PRESSURE", expected_pressure)

    def test_GIVEN_pressure2_with_no_decimal_places_set_WHEN_read_THEN_pressure2_is_as_expected(self):
        expected_pressure = 7
        self._set_pressure(expected_pressure, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:PRESSURE", expected_pressure)

    def test_GIVEN_pressure2_under_range_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.UNDER_RANGE
        expected_error_str = ErrorStrings.UNDER_RANGE
        expected_alarm = ChannelAccess.ALARM_MINOR
        self._set_error(expected_error, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("2:ERROR", expected_alarm)

    def test_GIVEN_pressure2_over_range_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.OVER_RANGE
        expected_error_str = ErrorStrings.OVER_RANGE
        expected_alarm = ChannelAccess.ALARM_MINOR
        self._set_error(expected_error, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("2:ERROR", expected_alarm)

    def test_GIVEN_pressure2_sensor_error_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.SENSOR_ERROR
        expected_error_str = ErrorStrings.SENSOR_ERROR
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("2:ERROR", expected_alarm)

    def test_GIVEN_pressure2_sensor_off_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.SENSOR_OFF
        expected_error_str = ErrorStrings.SENSOR_OFF
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("2:ERROR", expected_alarm)

    def test_GIVEN_pressure2_no_sensor_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.NO_SENSOR
        expected_error_str = ErrorStrings.NO_SENSOR
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("2:ERROR", expected_alarm)

    def test_GIVEN_pressure2_identification_error_set_WHEN_read_THEN_error(self):
        expected_error = ErrorFlags.IDENTIFICATION_ERROR
        expected_error_str = ErrorStrings.IDENTIFICATION_ERROR
        expected_alarm = ChannelAccess.ALARM_MAJOR
        self._set_error(expected_error, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("2:ERROR", expected_error_str)
        self.ca.assert_pv_alarm_is("2:ERROR", expected_alarm)

    def test_GIVEN_units_set_WHEN_read_THEN_units_are_as_expected(self):
        expected_units = UnitFlags.PA
        expected_unit_str = UnitStrings.PA
        self._set_units(expected_units)

        self.ca.assert_that_pv_is("UNITS", expected_unit_str)

    def test_WHEN_write_units_THEN_units_are_as_expected(self):
        expected_units = UnitFlags.PA
        expected_unit_str = UnitStrings.PA

        self.ca.set_pv_value("UNITS:SP", expected_units, wait=False)
        self.ca.assert_that_pv_is("UNITS", expected_unit_str)
