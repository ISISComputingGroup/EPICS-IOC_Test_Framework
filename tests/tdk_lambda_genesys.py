import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister

# MACROS to use for the IOC
# Macros may need to be formally set - check dbLoadRecords line in *ioc*_ddevsim_ioc.log file
MACROS = { "ADDR1": "1", "PORT1": "1"}


class OutputMode(object):
    VOLTAGE = "VOLTAGE"
    CURRENT = "CURRENT"


class Tdk_lambda_genesysTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tdk_lambda_genesys")
        self.ca = ChannelAccess(default_timeout=10)
        self.ca.wait_for("GENESYS_01:1:VOLT", timeout=30)

    def _write_voltage(self, expected_voltage):
        self._lewis.backdoor_set_on_device("voltage", expected_voltage)
        self.ca.set_pv_value("GENESYS_01:1:VOLT", expected_voltage)

    def _write_current(self, expected_current):
        self._lewis.backdoor_set_on_device("current", expected_current)
        self.ca.set_pv_value("GENESYS_01:1:CURR", expected_current)

    def _set_powerstate(self, expected_power):
        self._lewis.backdoor_set_on_device("powerstate", expected_power)

    @skipIf(IOCRegister.uses_rec_sim, "Uses LeWIS backdoor")
    def test_GIVEN_voltage_set_WHEN_read_THEN_voltage_is_as_expected(self):
        expected_voltage = 4.3
        self._write_voltage(expected_voltage)
        self.ca.assert_that_pv_is("GENESYS_01:1:VOLT", expected_voltage)

    @skipIf(IOCRegister.uses_rec_sim, "Uses LeWIS backdoor")
    def test_GIVEN_current_set_WHEN_read_THEN_current_is_as_expected(self):
        expected_current = 2
        self._write_current(expected_current)
        self.ca.assert_that_pv_is("GENESYS_01:1:CURR", expected_current)

    def test_GIVEN_setpoint_voltage_set_WHEN_read_THEN_setpoint_voltage_is_as_expected(self):
        current_voltage = self.ca.get_pv_value("GENESYS_01:1:VOLT:SP")
        self.ca.set_pv_value("GENESYS_01:1:VOLT:SP", current_voltage + 2.5)
        self.ca.assert_that_pv_is("GENESYS_01:1:VOLT:SP:RBV", current_voltage + 2.5)

    def test_GIVEN_setpoint_current_set_when_read_THEN_setpoint_current_is_as_expected(self):
        current_current = self.ca.get_pv_value("GENESYS_01:1:CURR:SP")
        self.ca.set_pv_value("GENESYS_01:1:CURR:SP", current_current + 5)
        self.ca.assert_that_pv_is("GENESYS_01:1:CURR:SP:RBV", current_current + 5)

    @skipIf(IOCRegister.uses_rec_sim, "Uses LeWIS backdoor")
    def test_GIVEN_powerstate_set_WHEN_read_THEN_powerstate_is_as_expected_ON(self):
        expected_power = "ON"
        self._set_powerstate(expected_power)
        self.ca.assert_that_pv_is("GENESYS_01:1:POWER", "On")

    @skipIf(IOCRegister.uses_rec_sim, "Uses LeWIS backdoor")
    def test_GIVEN_powerstate_set_WHEN_read_THEN_powerstate_is_as_expected_OFF(self):
        expected_power = "OFF"
        self._set_powerstate(expected_power)
        self.ca.assert_that_pv_is("GENESYS_01:1:POWER", "Off")

    def test_GIVEN_powerstate_set_pv_WHEN_read_THEN_pwoerstate_is_as_expected(self):
        expected_power = 1
        self.ca.set_pv_value("GENESYS_01:1:POWER:SP", expected_power)
        self.ca.assert_that_pv_is("GENESYS_01:1:POWER", "On")
