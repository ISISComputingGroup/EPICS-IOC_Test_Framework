import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# MACROS to use for the IOC
chopper_name = "C01"
MACROS = {"ADDR": chopper_name}

# Device prefix
DEVICE_PREFIX = "FZJDDFCH_01"

OK_NOK = {True: "OK", False: "NOK"}
ON_OFF = {True: "ON", False: "OFF"}
START_STOP = {True: "START", False: "STOP"}
CW_CCW = {True: "CW", False: "CCW"}


# SIMULATED_VALUES = { backdoor_parameter, pv_name, true_value, false_value }

SIMULATED_VALUES = {
    "frequency_reference": ("frequency_reference", "SIM:FREQ:REF"),
    "frequency_setpoint": ("frequency_setpoint", "SIM:FREQ:SP:RBV"),
    "frequency": ("frequency", "SIM:FREQ"),
    "phase_setpoint": ("phase_setpoint", "SIM:PHAS:SP:RBV"),
    "phase": ("phase", "SIM:PHAS"),
    "phase_status_is_ok": ("phase_status_is_ok", "SIM:PHAS:STAT", OK_NOK[True], OK_NOK[False]),
    "magnetic_bearing_is_on": ("magnetic_bearing_is_on", "SIM:MB", ON_OFF[True], ON_OFF[False]),
    "magnetic_bearing_status_is_ok": ("magnetic_bearing_status_is_ok", "SIM:MB:STAT", OK_NOK[True], OK_NOK[False]),
    "magnetic_bearing_integrator": ("magnetic_bearing_integrator", "SIM:MB:INT"),
    "drive_is_on": ("drive_is_on", "SIM:DRIVE", ON_OFF[True], ON_OFF[False]),
    "drive_mode_is_start": ("drive_mode_is_start", "SIM:DRIVE:MODE", START_STOP[True], START_STOP[False]),
    "drive_l1_current": ("drive_l1_current", "SIM:DRIVE:L1:CURR"),
    "drive_l2_current": ("drive_l2_current", "SIM:DRIVE:L2:CURR"),
    "drive_l3_current": ("drive_l3_current", "SIM:DRIVE:L3:CURR"),
    "drive_direction_is_cw": ("drive_direction_is_cw", "SIM:DRIVE:DIR", CW_CCW[True], CW_CCW[False]),
    "parked_open_status_is_ok": ("parked_open_status_is_ok", "SIM:PARKED:OPEN:STAT", OK_NOK[True], OK_NOK[False]),
    "drive_temperature": ("drive_temperature", "SIM:DRIVE:TEMP"),
    "input_clock": ("input_clock", "SIM:INPUTCLOCK"),
    "phase_outage": ("phase_outage", "SIM:PHAS:OUTAGE"),
    "master_chopper": ("master_chopper", "SIM:MASTER"),
    "logging_is_on": ("logging_is_on", "SIM:LOGGING", ON_OFF[True], ON_OFF[False]),
    "lmsr_status_is_ok": ("lmsr_status_is_ok", "SIM:LMSR:STAT", OK_NOK[True], OK_NOK[False]),
    "dsp_status_is_ok": ("dsp_status_is_ok", "SIM:DSP:STAT", OK_NOK[True], OK_NOK[False]),
    "interlock_er_status_is_ok": ("interlock_er_status_is_ok", "SIM:INTERLOCK:ER:STAT", OK_NOK[True], OK_NOK[False]),
    "interlock_vacuum_status_is_ok": ("interlock_vacuum_status_is_ok", "SIM:INTERLOCK:VAC:STAT", OK_NOK[True], 
                                      OK_NOK[False]),
    "interlock_frequency_monitoring_status_is_ok":
        ("interlock_frequency_monitoring_status_is_ok", "SIM:INTERLOCK:FREQMON:STAT", OK_NOK[True], OK_NOK[False]),
    "interlock_magnetic_bearing_amplifier_temperature_status_is_ok":
        ("interlock_magnetic_bearing_amplifier_temperature_status_is_ok", "SIM:INTERLOCK:MB:AMP:TEMP:STAT", OK_NOK[True], 
         OK_NOK[False]),
    "interlock_magnetic_bearing_amplifier_current_status_is_ok":
        ("interlock_magnetic_bearing_amplifier_current_status_is_ok", "SIM:INTERLOCK:MB:AMP:CURR:STAT", OK_NOK[True], 
         OK_NOK[False]),
    "interlock_drive_amplifier_temperature_status_is_ok":
        ("interlock_drive_amplifier_temperature_status_is_ok", "SIM:INTERLOCK:DRIVE:AMP:TEMP:STAT", OK_NOK[True], 
         OK_NOK[False]),
    "interlock_drive_amplifier_current_status_is_ok":
        ("interlock_drive_amplifier_current_status_is_ok", "SIM:INTERLOCK:DRIVE:AMP:CURR:STAT", OK_NOK[True], 
         OK_NOK[False]),
    "interlock_ups_status_is_ok": ("interlock_ups_status_is_ok", "SIM:INTERLOCK:UPS:STAT", OK_NOK[True], OK_NOK[False])
}


class Fzj_dd_fermi_chopperTests(unittest.TestCase):
    """
    Tests for the FZJ Digital Drive Fermi Chopper Controller
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("fzj_dd_fermi_chopper")

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("chopper_name", chopper_name)
        self._lewis.backdoor_command(["device", "reset"])

#   Command definitions:
    def _set_simulated_value(self, parameter, value):
        simulated_value = SIMULATED_VALUES[parameter]
        if len(simulated_value) == 4:
            backdoor_parameter, pv_name, true_value, false_value = simulated_value
            self._ioc.set_simulated_value(pv_name, true_value if value else false_value)
        else:
            backdoor_parameter, pv_name = simulated_value
            self._ioc.set_simulated_value(pv_name, value)
        self._lewis.backdoor_set_on_device(backdoor_parameter, value)


#   Tests:

    def test_GIVEN_frequency_reference_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 50.62
        self._set_simulated_value("frequency_reference", expected_value)

        self.ca.assert_that_pv_is("FREQ:REF", expected_value)
        self.ca.assert_pv_alarm_is("FREQ:REF", ChannelAccess.ALARM_NONE)

    def test_GIVEN_frequency_setpoint_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 60.97
        self._set_simulated_value("frequency_setpoint", expected_value)

        self.ca.assert_that_pv_is("FREQ:SP:RBV", expected_value)
        self.ca.assert_pv_alarm_is("FREQ:SP:RBV", ChannelAccess.ALARM_NONE)

    def test_GIVEN_frequency_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 35.72
        self._set_simulated_value("frequency", expected_value)

        self.ca.assert_that_pv_is("FREQ", expected_value)
        self.ca.assert_pv_alarm_is("FREQ", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_setpoint_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 45.27
        self._set_simulated_value("phase_setpoint", expected_value)

        self.ca.assert_that_pv_is("PHAS:SP:RBV", expected_value)
        self.ca.assert_pv_alarm_is("PHAS:SP:RBV", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 65.72
        self._set_simulated_value("phase", expected_value)

        self.ca.assert_that_pv_is("PHAS", expected_value)
        self.ca.assert_pv_alarm_is("PHAS", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("phase_status_is_ok", boolean_value)
    
            self.ca.assert_that_pv_is("PHAS:STAT", expected_value)
            self.ca.assert_pv_alarm_is("PHAS:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_magnetic_bearing_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("magnetic_bearing_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("MB:STAT", expected_value)
            self.ca.assert_pv_alarm_is("MB:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_magnetic_bearing_integrator_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = -27.4
        self._set_simulated_value("magnetic_bearing_integrator", expected_value)

        self.ca.assert_that_pv_is("MB:INT", expected_value)
        self.ca.assert_pv_alarm_is("MB:INT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_magnetic_bearing_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in ON_OFF.items():
            self._set_simulated_value("magnetic_bearing_is_on", boolean_value)

            self.ca.assert_that_pv_is("MB", expected_value)
            self.ca.assert_pv_alarm_is("MB", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in ON_OFF.items():
            self._set_simulated_value("drive_is_on", boolean_value)

            self.ca.assert_that_pv_is("DRIVE", expected_value)
            self.ca.assert_pv_alarm_is("DRIVE", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_mode_WHEN_read_all_status_THEN_value_is_as_expected(self):
        for boolean_value, expected_value in START_STOP.items():
            self._set_simulated_value("drive_mode_is_start", boolean_value)

            self.ca.assert_that_pv_is("DRIVE:MODE", expected_value)
            self.ca.assert_pv_alarm_is("DRIVE:MODE", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_l1_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 9.62
        self._set_simulated_value("drive_l1_current", expected_value)

        self.ca.assert_that_pv_is("DRIVE:L1:CURR", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:L1:CURR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_l2_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 2.74
        self._set_simulated_value("drive_l2_current", expected_value)

        self.ca.assert_that_pv_is("DRIVE:L2:CURR", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:L2:CURR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_l3_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 12.48
        self._set_simulated_value("drive_l3_current", expected_value)

        self.ca.assert_that_pv_is("DRIVE:L3:CURR", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:L3:CURR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_direction_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in CW_CCW.items():
            self._set_simulated_value("drive_direction_is_cw", boolean_value)

            self.ca.assert_that_pv_is("DRIVE:DIR", expected_value)
            self.ca.assert_pv_alarm_is("DRIVE:DIR", ChannelAccess.ALARM_NONE)

    def test_GIVEN_parked_open_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("parked_open_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("PARKED:OPEN:STAT", expected_value)
            self.ca.assert_pv_alarm_is("PARKED:OPEN:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_drive_temperature_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 86.31
        self._set_simulated_value("drive_temperature", expected_value)

        self.ca.assert_that_pv_is("DRIVE:TEMP", expected_value)
        self.ca.assert_pv_alarm_is("DRIVE:TEMP", ChannelAccess.ALARM_NONE)

    def test_GIVEN_input_clock_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 34.94
        self._set_simulated_value("input_clock", expected_value)

        self.ca.assert_that_pv_is("INPUTCLOCK", expected_value)
        self.ca.assert_pv_alarm_is("INPUTCLOCK", ChannelAccess.ALARM_NONE)

    def test_GIVEN_phase_outage_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 354.71
        self._set_simulated_value("phase_outage", expected_value)

        self.ca.assert_that_pv_is("PHAS:OUTAGE", expected_value)
        self.ca.assert_pv_alarm_is("PHAS:OUTAGE", ChannelAccess.ALARM_NONE)

    def test_GIVEN_master_chopper_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = "C2B"
        self._set_simulated_value("master_chopper", expected_value)

        self.ca.assert_that_pv_is("MASTER", expected_value)
        self.ca.assert_pv_alarm_is("MASTER", ChannelAccess.ALARM_NONE)

    def test_GIVEN_logging_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in ON_OFF.items():
            self._set_simulated_value("logging_is_on", boolean_value)

            self.ca.assert_that_pv_is("LOGGING", expected_value)
            self.ca.assert_pv_alarm_is("LOGGING", ChannelAccess.ALARM_NONE)

    def test_GIVEN_lmsr_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("lmsr_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("LMSR:STAT", expected_value)
            self.ca.assert_pv_alarm_is("LMSR:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_dsp_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("dsp_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("DSP:STAT", expected_value)
            self.ca.assert_pv_alarm_is("DSP:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_er_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_er_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:ER:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:ER:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_vacuum_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_vacuum_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:VAC:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:VAC:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_frequency_monitoring_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_frequency_monitoring_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:FREQMON:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:FREQMON:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_magnetic_bearing_amplifier_temperature_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_magnetic_bearing_amplifier_temperature_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:MB:AMP:TEMP:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:MB:AMP:TEMP:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_magnetic_bearing_amplifier_current_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_magnetic_bearing_amplifier_current_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:MB:AMP:CURR:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:MB:AMP:CURR:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_drive_amplifier_temperature_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_drive_amplifier_temperature_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:DRIVE:AMP:TEMP:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:DRIVE:AMP:TEMP:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_interlock_drive_amplifier_current_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_drive_amplifier_current_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:DRIVE:AMP:CURR:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:DRIVE:AMP:CURR:STAT", ChannelAccess.ALARM_NONE)

    def test_GIVEN_ups_status_WHEN_read_all_status_is_ok_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_ups_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:UPS:STAT", expected_value)
            self.ca.assert_pv_alarm_is("INTERLOCK:UPS:STAT", ChannelAccess.ALARM_NONE)

    # ***** Test set commands *****

    # Frequency

    def test_WHEN_frequency_setpoint_is_set_THEN_readback_updates(self):
        frequency = 150
        frequency_as_string = str(frequency)
        self.ca.set_pv_value("FREQ:SP", frequency_as_string)

        self.ca.assert_that_pv_is("FREQ:SP", frequency_as_string)
        self.ca.assert_pv_alarm_is("FREQ:SP", self.ca.ALARM_NONE)
        self.ca.assert_that_pv_is("FREQ:SP:RBV", frequency)
        self.ca.assert_pv_alarm_is("FREQ:SP:RBV", self.ca.ALARM_NONE)

    def test_GIVEN_error_WHEN_set_frequency_THEN_error_is_handled(self):
        frequency = 150
        frequency_as_string = str(frequency)
        expected_error = "07;C01NOK;RATIO_SPEED_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_frequency", expected_error)
        self.ca.set_pv_value("FREQ:SP", frequency_as_string)

        self.ca.assert_pv_alarm_is("FREQ:SP", self.ca.ALARM_INVALID)
        self.ca.assert_that_pv_is("FREQ:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_frequency_THEN_error_is_cleared(self):
        frequency = 150
        frequency_as_string = str(frequency)
        expected_error = "07;C01NOK;RATIO_SPEED_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_frequency", expected_error)
        self.ca.set_pv_value("FREQ:SP", frequency_as_string)
        self.ca.assert_pv_alarm_is("FREQ:SP", self.ca.ALARM_INVALID)
        self.ca.assert_that_pv_is("FREQ:SP:ERROR", expected_error)
        self._lewis.backdoor_set_on_device("error_on_set_frequency", None)

        self.ca.set_pv_value("FREQ:SP", frequency_as_string)

        self.ca.assert_that_pv_is("FREQ:SP:ERROR", "")

    #  Phase

    def test_WHEN_phase_setpoint_is_set_THEN_readback_updates(self):
        phase = 243.85
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_that_pv_is("PHAS:SP", phase)
        self.ca.assert_pv_alarm_is("PHAS:SP", self.ca.ALARM_NONE)
        self.ca.assert_that_pv_is("PHAS:SP:RBV", phase)
        self.ca.assert_pv_alarm_is("PHAS:SP:RBV", self.ca.ALARM_NONE)

    def test_GIVEN_error_WHEN_set_phase_THEN_error_is_handled(self):
        phase = 243.85
        expected_error = "09;CxxNOK;SETPOINT_PHASE_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_phase", expected_error)
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_pv_alarm_is("PHAS:SP", self.ca.ALARM_INVALID)
        self.ca.assert_that_pv_is("PHAS:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_phase_THEN_error_is_cleared(self):
        phase = 243.85
        expected_error = "09;CxxNOK;SETPOINT_PHASE_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_phase", expected_error)
        self.ca.set_pv_value("PHAS:SP", phase)
        self.ca.assert_pv_alarm_is("PHAS:SP", self.ca.ALARM_INVALID)
        self.ca.assert_that_pv_is("PHAS:SP:ERROR", expected_error)
        self._lewis.backdoor_set_on_device("error_on_set_phase", None)

        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_that_pv_is("PHAS:SP:ERROR", "")

    # Magnetic Bearing

    def test_WHEN_magnetic_bearing_is_set_THEN_readback_updates(self):
        for magnetic_bearing in [ON_OFF[True], ON_OFF[False]]:
            self.ca.set_pv_value("MB:SP", magnetic_bearing)

            self.ca.assert_that_pv_is("MB:SP", magnetic_bearing)
            self.ca.assert_pv_alarm_is("MB:SP", self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is("MB", magnetic_bearing)
            self.ca.assert_pv_alarm_is("MB", self.ca.ALARM_NONE)

    def test_GIVEN_error_WHEN_set_magnetic_bearing_is_on_THEN_error_is_handled(self):
        for magnetic_bearing in [ON_OFF[True], ON_OFF[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_magnetic_bearing", expected_error)
            self.ca.set_pv_value("MB:SP", magnetic_bearing)

            self.ca.assert_pv_alarm_is("MB:SP", self.ca.ALARM_INVALID)
            self.ca.assert_that_pv_is("MB:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_magnetic_bearing_is_on_THEN_error_is_cleared(self):
        for magnetic_bearing in [ON_OFF[True], ON_OFF[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_magnetic_bearing", expected_error)
            self.ca.set_pv_value("MB:SP", magnetic_bearing)
            self.ca.assert_pv_alarm_is("MB:SP", self.ca.ALARM_INVALID)
            self.ca.assert_that_pv_is("MB:SP:ERROR", expected_error)
            self._lewis.backdoor_set_on_device("error_on_set_magnetic_bearing", None)

            self.ca.set_pv_value("MB:SP", magnetic_bearing)

            self.ca.assert_that_pv_is("MB:SP:ERROR", "")

    # Drive

    def test_WHEN_drive_mode_is_set_THEN_readback_updates(self):
        for drive_mode in [START_STOP[True], START_STOP[False]]:
            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)

            self.ca.assert_that_pv_is("DRIVE:MODE:SP", drive_mode)
            self.ca.assert_pv_alarm_is("DRIVE:MODE:SP", self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is("DRIVE:MODE", drive_mode)
            self.ca.assert_pv_alarm_is("DRIVE:MODE", self.ca.ALARM_NONE)

    def test_GIVEN_error_WHEN_set_drive_mode_is_start_THEN_error_is_handled(self):
        for drive_mode in [START_STOP[True], START_STOP[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_drive_mode", expected_error)
            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)

            self.ca.assert_pv_alarm_is("DRIVE:MODE:SP", self.ca.ALARM_INVALID)
            self.ca.assert_that_pv_is("DRIVE:MODE:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_drive_mode_is_start_THEN_error_is_cleared(self):
        for drive_mode in [START_STOP[True], START_STOP[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_drive_mode", expected_error)
            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)
            self.ca.assert_pv_alarm_is("DRIVE:MODE:SP", self.ca.ALARM_INVALID)
            self.ca.assert_that_pv_is("DRIVE:MODE:SP:ERROR", expected_error)
            self._lewis.backdoor_set_on_device("error_on_set_drive_mode", None)

            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)

            self.ca.assert_that_pv_is("DRIVE:MODE:SP:ERROR", "")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_device_is_not_communicating_WHEN_read_all_status_THEN_values_have_error(self):
        self._lewis.backdoor_set_on_device("disconnected", True)

        for pv in ["FREQ:REF",
                   "FREQ:SP:RBV",
                   "FREQ",
                   "PHAS:SP:RBV",
                   "PHAS",
                   "PHAS:STAT",
                   "MB",
                   "MB:STAT",
                   "MB:INT",
                   "DRIVE",
                   "DRIVE:MODE",
                   "DRIVE:L1:CURR",
                   "DRIVE:L2:CURR",
                   "DRIVE:L3:CURR",
                   "DRIVE:DIR",
                   "PARKED:OPEN:STAT",
                   "DRIVE:TEMP",
                   "INPUTCLOCK",
                   "PHAS:OUTAGE",
                   "MASTER",
                   "LOGGING",
                   "LMSR:STAT",
                   "DSP:STAT",
                   "INTERLOCK:ER:STAT",
                   "INTERLOCK:VAC:STAT",
                   "INTERLOCK:FREQMON:STAT",
                   "INTERLOCK:MB:AMP:TEMP:STAT",
                   "INTERLOCK:MB:AMP:CURR:STAT",
                   "INTERLOCK:DRIVE:AMP:TEMP:STAT",
                   "INTERLOCK:DRIVE:AMP:CURR:STAT",
                   "INTERLOCK:UPS:STAT"]:

            self.ca.assert_pv_alarm_is(pv, ChannelAccess.ALARM_INVALID)
