import unittest
from unittest import skipIf

import datetime

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# MACROS to use for the IOC
MACROS = {}

# Device prefix
DEVICE_PREFIX = "FZJDDFCH_01"


class Fzj_dd_fermi_chopperTests(unittest.TestCase):
    """
    Tests for the FZJ Digital Drive Fermi Chopper Controller
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("fzj_dd_fermi_chopper")

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        # self._lewis.backdoor_set_on_device("address", ADDRESS)
        self._lewis.backdoor_command(["device", "reset"])

#   Command definitions:

    def _set_value(self, expected_value):

        self._lewis.backdoor_set_on_device("magnetic_bearing_status", expected_value)
        self._ioc.set_simulated_value("SIM:MB:STATUS", expected_value)

    def _set_frequency_reference(self, frequency_reference):

        self._lewis.backdoor_set_on_device("frequency_reference", frequency_reference)
        self._ioc.set_simulated_value("SIM:FREQ:REF", frequency_reference)

    def _set_frequency_setpoint(self, frequency_setpoint):

        self._lewis.backdoor_set_on_device("frequency_setpoint", frequency_setpoint)
        self._ioc.set_simulated_value("SIM:FREQ:SP:RBV", frequency_setpoint)

    def _set_frequency(self, frequency):
        self._lewis.backdoor_set_on_device("frequency", frequency)
        self._ioc.set_simulated_value("SIM:FREQ", frequency)

    def _set_phase_setpoint(self, phase_setpoint):
        self._lewis.backdoor_set_on_device("phase_setpoint", phase_setpoint)
        self._ioc.set_simulated_value("SIM:PHAS:SP:RBV", phase_setpoint)

    def _set_phase(self, phase):
        self._lewis.backdoor_set_on_device("phase", phase)
        self._ioc.set_simulated_value("SIM:PHAS", phase)

    def _set_phase_status(self, phase_status):
        self._lewis.backdoor_set_on_device("phase_status", phase_status)
        self._ioc.set_simulated_value("SIM:PHAS:STATUS", phase_status)

    def _set_magnetic_bearing(self, magnetic_bearing):
        self._lewis.backdoor_set_on_device("magnetic_bearing", magnetic_bearing)
        self._ioc.set_simulated_value("SIM:MB", magnetic_bearing)

    def _set_magnetic_bearing_status(self, magnetic_bearing_status):
        self._lewis.backdoor_set_on_device("magnetic_bearing_status", magnetic_bearing_status)
        self._ioc.set_simulated_value("SIM:MB:STATUS", magnetic_bearing_status)

    def _set_magnetic_bearing_integrator(self, magnetic_bearing_integrator):
        self._lewis.backdoor_set_on_device("magnetic_bearing_integrator", magnetic_bearing_integrator)
        self._ioc.set_simulated_value("SIM:MB:INT", magnetic_bearing_integrator)

    def _set_drive(self, drive):
        self._lewis.backdoor_set_on_device("drive", drive)
        self._ioc.set_simulated_value("SIM:DRIVE", drive)

    def _set_drive_status(self, drive_status):
        self._lewis.backdoor_set_on_device("drive_status", drive_status)
        self._ioc.set_simulated_value("SIM:DRIVE:STATUS", drive_status)

    def _set_drive_l1_current(self, drive_l1_current):
        self._lewis.backdoor_set_on_device("drive_l1_current", drive_l1_current)
        self._ioc.set_simulated_value("SIM:DRIVE:L1:CURR", drive_l1_current)

    def _set_drive_l2_current(self, drive_l2_current):
        self._lewis.backdoor_set_on_device("drive_l2_current", drive_l2_current)
        self._ioc.set_simulated_value("SIM:DRIVE:L2:CURR", drive_l2_current)

    def _set_drive_l3_current(self, drive_l3_current):
        self._lewis.backdoor_set_on_device("drive_l3_current", drive_l3_current)
        self._ioc.set_simulated_value("SIM:DRIVE:L3:CURR", drive_l3_current)

    def _set_drive_direction(self, drive_direction):
        self._lewis.backdoor_set_on_device("drive_direction", drive_direction)
        self._ioc.set_simulated_value("SIM:DRIVE:DIR", drive_direction)

    def _set_parked_open_status(self, parked_open_status):
        self._lewis.backdoor_set_on_device("parked_open_status", parked_open_status)
        self._ioc.set_simulated_value("SIM:PARKED:OPEN:STATUS", parked_open_status)

    def _set_drive_temperature(self, drive_temperature):
        self._lewis.backdoor_set_on_device("drive_temperature", drive_temperature)
        self._ioc.set_simulated_value("SIM:DRIVE:TEMP", drive_temperature)

    def _set_input_clock(self, input_clock):
        self._lewis.backdoor_set_on_device("input_clock", input_clock)
        self._ioc.set_simulated_value("SIM:INPUTCLOCK", input_clock)

    def _set_phase_outage(self, phase_outage):
        self._lewis.backdoor_set_on_device("phase_outage", phase_outage)
        self._ioc.set_simulated_value("SIM:PHAS:OUTAGE", phase_outage)

    def _set_master_chopper(self, master_chopper):
        self._lewis.backdoor_set_on_device("master_chopper", master_chopper)
        self._ioc.set_simulated_value("SIM:MASTER", master_chopper)

    def _set_logging(self, logging):
        self._lewis.backdoor_set_on_device("logging", logging)
        self._ioc.set_simulated_value("SIM:LOGGING", logging)

    def _set_lmsr_status(self, lmsr_status):
        self._lewis.backdoor_set_on_device("lmsr_status", lmsr_status)
        self._ioc.set_simulated_value("SIM:LMSR:STATUS", lmsr_status)

    def _set_dsp_status(self, dsp_status):
        self._lewis.backdoor_set_on_device("dsp_status", dsp_status)
        self._ioc.set_simulated_value("SIM:DSP:STATUS", dsp_status)

    def _set_interlock_er_status(self, interlock_er_status):
        self._lewis.backdoor_set_on_device("interlock_er_status", interlock_er_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:ER:STATUS", interlock_er_status)

    def _set_interlock_vacuum_status(self, interlock_vacuum_status):
        self._lewis.backdoor_set_on_device("interlock_vacuum_status", interlock_vacuum_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:VAC:STATUS", interlock_vacuum_status)

    def _set_interlock_frequency_monitoring_status(self, interlock_frequency_monitoring_status):
        self._lewis.backdoor_set_on_device("interlock_frequency_monitoring_status", interlock_frequency_monitoring_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:FREQMON:STATUS", interlock_frequency_monitoring_status)

    def _set_interlock_magnetic_bearing_amplifier_temperature_status(self, interlock_magnetic_bearing_amplifier_temperature_status):
        self._lewis.backdoor_set_on_device("interlock_magnetic_bearing_amplifier_temperature_status", interlock_magnetic_bearing_amplifier_temperature_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:MB:AMP:TEMP:STATUS", interlock_magnetic_bearing_amplifier_temperature_status)

    def _set_interlock_magnetic_bearing_amplifier_current_status(self, interlock_magnetic_bearing_amplifier_current_status):
        self._lewis.backdoor_set_on_device("interlock_magnetic_bearing_amplifier_current_status", interlock_magnetic_bearing_amplifier_current_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:MB:AMP:CURR:STATUS", interlock_magnetic_bearing_amplifier_current_status)

    def _set_interlock_drive_amplifier_temperature_status(self, interlock_drive_amplifier_temperature_status):
        self._lewis.backdoor_set_on_device("interlock_drive_amplifier_temperature_status", interlock_drive_amplifier_temperature_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:DRIVE:AMP:TEMP:STATUS", interlock_drive_amplifier_temperature_status)

    def _set_interlock_drive_amplifier_current_status(self, interlock_drive_amplifier_current_status):
        self._lewis.backdoor_set_on_device("interlock_drive_amplifier_current_status", interlock_drive_amplifier_current_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:DRIVE:AMP:CURR:STATUS", interlock_drive_amplifier_current_status)

    def _set_interlock_ups_status(self, interlock_ups_status):
        self._lewis.backdoor_set_on_device("interlock_ups_status", interlock_ups_status)
        self._ioc.set_simulated_value("SIM:INTERLOCK:UPS:STATUS", interlock_ups_status)

#   Tests:

    def test_GIVEN_frequency_reference_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 50.62
        self._set_frequency_reference(expected_value)

        self.ca.assert_that_pv_is("FREQ:REF", expected_value)
        self.ca.assert_pv_alarm_is("FREQ:REF", ChannelAccess.ALARM_NONE)

    def test_GIVEN_frequency_setpoint_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 60.97
        self._set_frequency_setpoint(expected_value)

        self.ca.assert_that_pv_is("FREQ:SP:RBV", expected_value)
        self.ca.assert_pv_alarm_is("FREQ:SP:RBV", ChannelAccess.ALARM_NONE)

    def test_GIVEN_frequency_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 35.72
        self._set_frequency(expected_value)

        self.ca.assert_that_pv_is("FREQ", expected_value)
        self.ca.assert_pv_alarm_is("FREQ", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_setpoint_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 45.27
        self._set_phase_setpoint(expected_value)

        self.ca.assert_that_pv_is("PHAS:SP:RBV", expected_value)
        self.ca.assert_pv_alarm_is("PHAS:SP:RBV", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 65.72
        self._set_phase(expected_value)

        self.ca.assert_that_pv_is("PHAS", expected_value)
        self.ca.assert_pv_alarm_is("PHAS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "OK"
        self._set_phase_status(expected_value)

        self.ca.assert_that_pv_is("PHAS:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("PHAS:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_magnetic_bearing_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "ON"
        self._set_magnetic_bearing(expected_value)

        self.ca.assert_that_pv_is("MB", expected_value)
        self.ca.assert_pv_alarm_is("MB", ChannelAccess.ALARM_NONE)

    def test_GIVEN_magnetic_bearing_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "OK"
        self._set_magnetic_bearing_status(expected_value)

        self.ca.assert_that_pv_is("MB:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("MB:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_magnetic_bearing_integrator_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = -27.4
        self._set_magnetic_bearing_integrator(expected_value)

        self.ca.assert_that_pv_is("MB:INT", expected_value)
        self.ca.assert_pv_alarm_is("MB:INT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "ON"
        self._set_drive(expected_value)

        self.ca.assert_that_pv_is("DRIVE", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "STOP"
        self._set_drive_status(expected_value)

        self.ca.assert_that_pv_is("DRIVE:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_l1_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 9.62
        self._set_drive_l1_current(expected_value)

        self.ca.assert_that_pv_is("DRIVE:L1:CURR", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:L1:CURR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_l2_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 2.74
        self._set_drive_l2_current(expected_value)

        self.ca.assert_that_pv_is("DRIVE:L2:CURR", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:L2:CURR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_l3_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 12.48
        self._set_drive_l3_current(expected_value)

        self.ca.assert_that_pv_is("DRIVE:L3:CURR", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:L3:CURR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_direction_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "CCW"
        self._set_drive_direction(expected_value)

        self.ca.assert_that_pv_is("DRIVE:DIR", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:DIR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_parked_open_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_parked_open_status(expected_value)

        self.ca.assert_that_pv_is("PARKED:OPEN:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("PARKED:OPEN:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_temperature_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 86.31
        self._set_drive_temperature(expected_value)

        self.ca.assert_that_pv_is("DRIVE:TEMP", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:TEMP", ChannelAccess.ALARM_NONE)

    def test_GIVEN_input_clock_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 34.94
        self._set_input_clock(expected_value)

        self.ca.assert_that_pv_is("INPUTCLOCK", expected_value)
        self.ca.assert_pv_alarm_is("INPUTCLOCK", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_outage_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 354.71
        self._set_phase_outage(expected_value)

        self.ca.assert_that_pv_is("PHAS:OUTAGE", expected_value)
        self.ca.assert_pv_alarm_is("PHAS:OUTAGE", ChannelAccess.ALARM_NONE)

    def test_GIVEN_master_chopper_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = "C2B"
        self._set_master_chopper(expected_value)

        self.ca.assert_that_pv_is("MASTER", expected_value)
        self.ca.assert_pv_alarm_is("MASTER", ChannelAccess.ALARM_NONE)

    def test_GIVEN_logging_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "OFF"
        self._set_logging(expected_value)

        self.ca.assert_that_pv_is("LOGGING", expected_value)
        self.ca.assert_pv_alarm_is("LOGGING", ChannelAccess.ALARM_NONE)

    def test_GIVEN_lmsr_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_lmsr_status(expected_value)

        self.ca.assert_that_pv_is("LMSR:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("LMSR:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_dsp_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_dsp_status(expected_value)

        self.ca.assert_that_pv_is("DSP:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("DSP:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_er_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_er_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:ER:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:ER:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_vacuum_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_vacuum_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:VAC:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:VAC:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_frequency_monitoring_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_frequency_monitoring_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:FREQMON:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:FREQMON:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_magnetic_bearing_amplifier_temperature_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_magnetic_bearing_amplifier_temperature_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:MB:AMP:TEMP:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:MB:AMP:TEMP:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_magnetic_bearing_amplifier_current_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_magnetic_bearing_amplifier_current_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:MB:AMP:CURR:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:MB:AMP:CURR:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_drive_amplifier_temperature_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_drive_amplifier_temperature_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:DRIVE:AMP:TEMP:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:DRIVE:AMP:TEMP:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_drive_amplifier_current_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_drive_amplifier_current_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:DRIVE:AMP:CURR:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:DRIVE:AMP:CURR:STATUS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_ups_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        expected_value = "NOK"
        self._set_interlock_ups_status(expected_value)

        self.ca.assert_that_pv_is("INTERLOCK:UPS:STATUS", expected_value)
        self.ca.assert_pv_alarm_is("INTERLOCK:UPS:STATUS", ChannelAccess.ALARM_NONE)
