import unittest
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc


class OutputMode(object):
    VOLTAGE = "VOLTAGE"
    CURRENT = "CURRENT"


class Status(object):
    ON = "ON"
    OFF = "OFF"


class UnitFlags(object):
    VOLTAGE = 0
    CURRENT = 1
    ON = 1
    OFF = 0


class KepcoTests(unittest.TestCase):
    """
    Tests for the KEPCO.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("kepco")
        self.ca = ChannelAccess(default_timeout=30, device_prefix="KEPCO_01")
        self.ca.wait_for("VOLTAGE", timeout=30)

    def _write_voltage(self, expected_voltage):
        self._lewis.backdoor_set_on_device("voltage", expected_voltage)
        self._ioc.set_simulated_value("KEPCO_01:SIM:VOLTAGE", expected_voltage)

    def _write_current(self, expected_current):
        self._lewis.backdoor_set_on_device("current", expected_current)
        self._ioc.set_simulated_value("KEPCO_01:SIM:CURRENT", expected_current)

    def _set_IDN(self, expected_idn):
        self._lewis.backdoor_set_on_device("idn", expected_idn)
        self._ioc.set_simulated_value("KEPCO_01:SIM:IDN", expected_idn)

    def _set_output_mode(self, expected_output_mode):
        self._lewis.backdoor_set_on_device("output_mode", expected_output_mode)
        self._ioc.set_simulated_value("KEPCO_01:SIM:OUTPUTMODE", expected_output_mode)

    def _set_output_status(self, expected_output_status):
        self._lewis.backdoor_set_on_device("output_status", expected_output_status)

    def test_GIVEN_voltage_set_WHEN_read_THEN_voltage_is_as_expected(self):
        expected_voltage = 1.2
        self._write_voltage(expected_voltage)
        self.ca.assert_that_pv_is("VOLTAGE", expected_voltage)

    def test_GIVEN_current_set_WHEN_read_THEN_current_is_as_expected(self):
        expected_current = 1.5
        self._write_current(expected_current)
        self.ca.assert_that_pv_is("CURRENT", expected_current)

    def test_GIVEN_setpoint_voltage_set_WHEN_read_THEN_setpoint_voltage_is_as_expected(self):
        # Get current Voltage
        current_voltage = self.ca.get_pv_value("VOLTAGE")
        # Set new Voltage via SP
        self.ca.set_pv_value("VOLTAGE:SP", current_voltage + 5.0)
        # Check SP RBV matches new current
        self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", current_voltage + 5.0)

    def test_GIVEN_setpoint_current_set_WHEN_read_THEN_setpoint_current_is_as_expected(self):
        # Get current current
        current_current = self.ca.get_pv_value("CURRENT")
        # Set new Current via SP
        self.ca.set_pv_value("CURRENT:SP", current_current + 5.0)
        # Check SP RBV matches new current
        self.ca.assert_that_pv_is("CURRENT:SP:RBV", current_current + 5.0)

    def test_GIVEN_output_mode_set_WHEN_read_THEN_output_mode_is_as_expected(self):
        expected_output_mode_flag = UnitFlags.CURRENT
        expected_output_mode_str =  OutputMode.CURRENT
        self._set_output_mode(expected_output_mode_flag)
        # Check OUTPUT MODE matches new OUTPUT MODE
        self.ca.assert_that_pv_is("OUTPUTMODE", expected_output_mode_str)

    def test_GIVEN_output_status_set_WHEN_read_THEN_output_STATUS_is_as_expected(self):
        expected_output_status_flag = UnitFlags.ON
        expected_output_status_str = Status.ON
        self.ca.set_pv_value("OUTPUTSTATUS:SP", expected_output_status_flag, wait=False)
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", expected_output_status_str)

    def test_GIVEN_idn_set_WHEN_read_THEN_idn_is_as_expected(self):
        expected_idn = "000000000000000000111111111111111111111"
        self._set_IDN(expected_idn)
        # Made Proc field force scan as IDN scan is passive
        self.ca.set_pv_value("IDN.PROC", 1, wait=False)
        self.ca.assert_that_pv_is("IDN", expected_idn)
