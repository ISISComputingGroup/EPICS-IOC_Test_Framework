import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

from time import sleep


CALIBRATION_A = 1.23
CALIBRATION_B = -4.56

MACROS = { "CALIBRATION_A": str(CALIBRATION_A), "CALIBRATION_B": str(CALIBRATION_B)}

class IegTests(unittest.TestCase):
    """
    Tests for the IEG IOC.
    """

    operation_modes = [(1, "Pump, Purge & Fill"),
                       (2, "Pump"),
                       (3, "Gas Flow"),
                       (4, "Gas - Single Shot"),]

    error_codes = [(0, "No error"),
                   (2, "Samp vol: leak detected"),
                   (3, "Samp vol: no vacuum"),
                   (4, "Buff vol: did not fill"),
                   (5, "Samp vol: fill iterations"),
                   (6, "Samp vol: pump timeout"),
                   (7, "Samp vol: fill timeout"),
                   (8, "Buff or samp vol leak"),
                   (9, "Shot didn't raise press."),
                   (10, "Manual stop"),
                   (11, "Vacuum tank interlock"),
                   (12, "Samp vol: leak detected"),
                   (13, "Sensor broken/disconnect")]

    test_device_ids = [0, 123, 255]
    test_pressures = [0, 10, 1024]

    @staticmethod
    def _get_actual_from_raw(value):
        return value * CALIBRATION_A + CALIBRATION_B

    @staticmethod
    def _get_raw_from_actual(value):
        return int(round((value - CALIBRATION_B) - CALIBRATION_A))

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ieg")

        self.ca = ChannelAccess(device_prefix="IEG_01", default_timeout=20)
        self.ca.wait_for("DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_mode_setpoint_is_set_THEN_readback_updates(self):
        for set_val, return_val in self.operation_modes:
            self.ca.assert_setting_setpoint_sets_readback(set_val, set_point_pv="MODE:SP", readback_pv="MODE", expected_value=return_val)

    @skipIf(IOCRegister.uses_rec_sim, "Not implemented in recsim")
    def test_GIVEN_device_not_in_dormant_state_WHEN_kill_command_is_sent_THEN_device_goes_to_dormant_state(self):
        set_val, return_val = self.operation_modes[0]
        self.ca.assert_setting_setpoint_sets_readback(set_val, set_point_pv="MODE:SP", readback_pv="MODE", expected_value=return_val)

        self.ca.set_pv_value("ABORT", 1, wait=False)
        self.ca.assert_that_pv_is("MODE", "Dormant")

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_device_id_is_changed_on_device_THEN_device_id_pv_updates(self):
        for val in self.test_device_ids:
            self._lewis.backdoor_set_on_device("unique_id", val)
            self.ca.assert_that_pv_is("ID", val, timeout=30)
            self.ca.assert_pv_alarm_is("ID", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_valve_states_are_changed_on_device_THEN_valve_state_pv_updates(self):
        for gas_valve_open in [True, False]:
            self._lewis.backdoor_set_on_device("gas_valve_open", gas_valve_open)
            for buffer_valve_open in [True, False]:
                self._lewis.backdoor_set_on_device("buffer_valve_open", buffer_valve_open)
                for pump_valve_open in [True, False]:
                    self._lewis.backdoor_set_on_device("pump_valve_open", pump_valve_open)
                    self.ca.assert_that_pv_is_number("VALVESTATE.B0", 1 if pump_valve_open else 0)
                    self.ca.assert_that_pv_is_number("VALVESTATE.B1", 1 if buffer_valve_open else 0)
                    self.ca.assert_that_pv_is_number("VALVESTATE.B2", 1 if gas_valve_open else 0)
                    self.ca.assert_pv_alarm_is("VALVESTATE", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_valve_states_are_changed_on_device_THEN_valve_state_pv_updates(self):
        for error_num, error in self.error_codes:
            self._lewis.backdoor_set_on_device("error", error_num)
            self.ca.assert_that_pv_is("ERROR", error)
            self.ca.assert_pv_alarm_is("ERROR", self.ca.ALARM_MAJOR if error_num else self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_pressure_is_changed_on_device_THEN_raw_pressure_pv_updates(self):
        for pressure in self.test_pressures:
            self._lewis.backdoor_set_on_device("sample_pressure", pressure)
            self.ca.assert_that_pv_is("PRESSURE:RAW", pressure)
            self.ca.assert_pv_alarm_is("PRESSURE:RAW", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_pressure_and_upper_limit_are_changed_on_device_THEN_pressure_high_pv_updates(self):
        for pressure in self.test_pressures:
            self._lewis.backdoor_set_on_device("sample_pressure", pressure)
            for upper_limit in [pressure - 1, pressure + 1]:
                self._lewis.backdoor_set_on_device("sample_pressure_high_limit", upper_limit)
                self.ca.assert_that_pv_is("PRESSURE:HIGH",
                                          "Out of range" if pressure > upper_limit else "In range")
                self.ca.assert_pv_alarm_is("PRESSURE:HIGH",
                                           self.ca.ALARM_MINOR if pressure > upper_limit else self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_pressure_and_lower_limit_are_changed_on_device_THEN_pressure_low_pv_updates(self):
        for pressure in self.test_pressures:
            self._lewis.backdoor_set_on_device("sample_pressure", pressure)
            for lower_limit in [pressure - 1, pressure + 1]:
                self._lewis.backdoor_set_on_device("sample_pressure_low_limit", lower_limit)
                self.ca.assert_that_pv_is("PRESSURE:LOW",
                                          "Out of range" if pressure < lower_limit else "In range")
                self.ca.assert_pv_alarm_is("PRESSURE:LOW",
                                           self.ca.ALARM_MINOR if pressure < lower_limit else self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_buffer_pressure_high_is_changed_on_device_THEN_buffer_pressure_high_pv_updates(self):
        for value in [True, False]:
            self._lewis.backdoor_set_on_device("buffer_pressure_high", value)

            # Intentionally this way round - the manual
            # says that 0 means 'above high threshold' and 1 is 'below high threshold'
            self.ca.assert_that_pv_is("PRESSURE:BUFFER:HIGH",
                                      "Out of range" if value else "In range")
            self.ca.assert_pv_alarm_is("PRESSURE:BUFFER:HIGH",
                                       self.ca.ALARM_MINOR if value else self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_pressure_is_over_350_THEN_displayed_as_greater_than_350_mBar(self):
        self._lewis.backdoor_set_on_device("sample_pressure", self._get_raw_from_actual(400))
        self.ca.assert_that_pv_is("PRESSURE:GUI.OSV", "> 350 mbar")
        self.ca.assert_pv_alarm_is("PRESSURE:GUI", self.ca.ALARM_MAJOR)

    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_pressure_is_set_THEN_it_is_converted_correctly_using_the_calibration(self):
        for raw_pressure in self.test_pressures:
            actual_pressure = self._get_actual_from_raw(raw_pressure)

            self._lewis.backdoor_set_on_device("sample_pressure", raw_pressure)
            self.ca.assert_that_pv_is_number("PRESSURE", actual_pressure, tolerance=0.05)
            self.ca.assert_pv_alarm_is("PRESSURE", self.ca.ALARM_NONE if .0 < actual_pressure < 350 else self.ca.ALARM_MAJOR)
