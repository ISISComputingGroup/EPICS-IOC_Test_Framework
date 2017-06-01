import unittest
from unittest import skipIf

from utils.ioc_launcher import IOCRegister
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc

# MACROS to use for the IOC
MACROS = {}


class Tpg26xTests(unittest.TestCase):
    """
    Tests for the TPG26x
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tpg26x")

        self.ca = ChannelAccess()
        self.ca.wait_for("TPG26X_01:1:PRESSURE")

    def _set_pressure(self, expected_pressure, channel):
        pv = "TPG26X_01:SIM:{0:d}:PRESSURE".format(channel)
        prop = "pressure%d" % channel
        self._lewis.backdoor_set_on_device(prop, expected_pressure)
        self._ioc.set_simulated_value(pv, expected_pressure)

    def test_GIVEN_pressure1_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure, 1)

        self.ca.assert_that_pv_is("TPG26X_01:1:PRESSURE", expected_pressure)
        self.ca.assert_pv_alarm_is("TPG26X_01:1:PRESSURE", ChannelAccess.ALARM_NONE)
        self.ca.assert_that_pv_is("TPG26X_01:1:ERROR", "No Error")

    def test_GIVEN_negative_pressure1_set_WHEN_read_THEN_pressure1_is_as_expected(self):
        expected_pressure = -123.34
        self._set_pressure(expected_pressure, 1)

        self.ca.assert_that_pv_is("TPG26X_01:1:PRESSURE", expected_pressure)

    def test_GIVEN_pressure1_with_no_decimal_places_set_WHEN_read_THEN_pressure1_is_as_expected(self):
        expected_pressure = 7
        self._set_pressure(expected_pressure, 1)

        self.ca.assert_that_pv_is("TPG26X_01:1:PRESSURE", expected_pressure)

    def test_GIVEN_pressure2_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure, 2)

        self.ca.assert_that_pv_is("TPG26X_01:2:PRESSURE", expected_pressure)
        self.ca.assert_pv_alarm_is("TPG26X_01:2:PRESSURE", ChannelAccess.ALARM_NONE)
        self.ca.assert_that_pv_is("TPG26X_01:2:ERROR", "No Error")

    def test_GIVEN_negative_pressure2_set_WHEN_read_THEN_pressure2_is_as_expected(self):
        expected_pressure = -123.34
        self._set_pressure(expected_pressure, 2)

        self.ca.assert_that_pv_is("TPG26X_01:2:PRESSURE", expected_pressure)

    def test_GIVEN_pressure2_with_no_decimal_places_set_WHEN_read_THEN_pressure2_is_as_expected(self):
        expected_pressure = 7
        self._set_pressure(expected_pressure, 2)

        self.ca.assert_that_pv_is("TPG26X_01:2:PRESSURE", expected_pressure)

