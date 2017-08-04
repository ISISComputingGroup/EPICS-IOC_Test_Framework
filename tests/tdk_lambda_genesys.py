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
        self.ca.wait_for("GENESYS_01:1:VOLT", timeout=20)

    def _write_voltage(self, expected_voltage):
        self._lewis.backdoor_set_on_device("voltage", expected_voltage)
        self.ca.set_pv_value("GENESYS_01:1:VOLT", expected_voltage)

    def _write_current(self, expected_current):
        self._lewis.backdoor_set_on_device("current", expected_current)
        self.ca.set_pv_value("GENESYS_01:1:CURR", expected_current)

    def _set_powerstate(self, expected_state):
        self._lewis.backdoor_set_on_device("powerstate", expected_state)

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
        expected_voltage = self.ca.get_pv_value("GENESYS_01:1:VOLT:SP") + 2.5
        self.ca.assert_setting_setpoint_sets_readback(expected_voltage, "GENESYS_01:1:VOLT:SP:RBV",
                                                      "GENESYS_01:1:VOLT:SP")

    def test_GIVEN_setpoint_current_set_when_read_THEN_setpoint_current_is_as_expected(self):
        expected_current = self.ca.get_pv_value("GENESYS_01:1:CURR:SP") + 5
        self.ca.set_pv_value("GENESYS_01:1:CURR:SP", expected_current)
        self.ca.assert_that_pv_is("GENESYS_01:1:CURR:SP:RBV", expected_current)

    @skipIf(IOCRegister.uses_rec_sim, "Uses LeWIS backdoor")
    def test_GIVEN_state_set_WHEN_read_THEN_state_is_as_expected_ON(self):
        self._set_powerstate("ON")
        self.ca.assert_that_pv_is("GENESYS_01:1:POWER", "ON")

    @skipIf(IOCRegister.uses_rec_sim, "Uses LeWIS backdoor")
    def test_GIVEN_state_set_WHEN_read_THEN_state_is_as_expected_OFF(self):
        self._set_powerstate("OFF")
        self.ca.assert_that_pv_is("GENESYS_01:1:POWER", "OFF")

    def test_GIVEN_state_set_via_number_WHEN_read_THEN_state_is_as_expected(self):
        self.ca.set_pv_value("GENESYS_01:1:POWER:SP", 1)
        self.ca.assert_that_pv_is("GENESYS_01:1:POWER", "ON")
