import unittest
from unittest import skipIf

from utils.ioc_launcher import IOCRegister
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


class Tpg26xTests(unittest.TestCase):
    """
    Tests for the TPG26x
    """

    CHANNEL_ONE = 1
    CHANNEL_TWO = 2

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tpg26x")

        self.ca = ChannelAccess()
        self.ca.wait_for("TPG26X_01:1:PRESSURE")

    def _set_pressure(self, expected_pressure, channel):
        pv = "TPG26X_01:SIM:{0:d}:PRESSURE".format(channel)
        prop = "pressure%d" % channel
        self._lewis.backdoor_set_on_device(prop, expected_pressure)
        self._ioc.set_simulated_value(pv, expected_pressure)

    def _set_units(self, expected_units):
        self._lewis.backdoor_set_on_device("units", expected_units)
        self._ioc.set_simulated_value("TPG26X_01:SIM:UNITS", expected_units)

    def test_GIVEN_pressure1_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("TPG26X_01:1:PRESSURE", expected_pressure)
        self.ca.assert_pv_alarm_is("TPG26X_01:1:PRESSURE", ChannelAccess.ALARM_NONE)
        self.ca.assert_that_pv_is("TPG26X_01:1:ERROR", "No Error")

    def test_GIVEN_negative_pressure1_set_WHEN_read_THEN_pressure1_is_as_expected(self):
        expected_pressure = -123.34
        self._set_pressure(expected_pressure, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("TPG26X_01:1:PRESSURE", expected_pressure)

    def test_GIVEN_pressure1_with_no_decimal_places_set_WHEN_read_THEN_pressure1_is_as_expected(self):
        expected_pressure = 7
        self._set_pressure(expected_pressure, self.CHANNEL_ONE)

        self.ca.assert_that_pv_is("TPG26X_01:1:PRESSURE", expected_pressure)

    def test_GIVEN_pressure2_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("TPG26X_01:2:PRESSURE", expected_pressure)
        self.ca.assert_pv_alarm_is("TPG26X_01:2:PRESSURE", ChannelAccess.ALARM_NONE)
        self.ca.assert_that_pv_is("TPG26X_01:2:ERROR", "No Error")

    def test_GIVEN_negative_pressure2_set_WHEN_read_THEN_pressure2_is_as_expected(self):
        expected_pressure = -123.34
        self._set_pressure(expected_pressure, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("TPG26X_01:2:PRESSURE", expected_pressure)

    def test_GIVEN_pressure2_with_no_decimal_places_set_WHEN_read_THEN_pressure2_is_as_expected(self):
        expected_pressure = 7
        self._set_pressure(expected_pressure, self.CHANNEL_TWO)

        self.ca.assert_that_pv_is("TPG26X_01:2:PRESSURE", expected_pressure)

    def test_GIVEN_units_set_WHEN_read_THEN_units_is_as_expected(self):
        expected_units = UnitFlags.PA
        expected_unit_str = UnitStrings.PA
        self._set_units(expected_units)

        self.ca.assert_that_pv_is("TPG26X_01:UNITS", expected_unit_str)

