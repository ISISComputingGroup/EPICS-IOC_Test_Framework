import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

chopper_name = "C01"

# Device prefix
DEVICE_PREFIX = "FZJDDFCH_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FZJDDFCH"),
        "macros": {"ADDR": chopper_name},
        "emulator": "fzj_dd_fermi_chopper",
    },
]

TEST_MODES = [TestModes.DEVSIM]

OK_NOK = {True: "OK", False: "NOK"}
ON_OFF = {True: "ON", False: "OFF"}
START_STOP = {True: "START", False: "STOP"}
CW_CCW = {True: "CW", False: "CCW"}


# SIMULATED_VALUES = { backdoor_parameter, pv_name, true_value, false_value }

SIMULATED_VALUES = {
    "frequency_setpoint": ("frequency_setpoint", "SIM:FREQ:SP:RBV"),
    "frequency": ("frequency", "SIM:FREQ"),
    "phase_setpoint": ("phase_setpoint", "SIM:PHAS:SP:RBV"),
    "phase": ("phase", "SIM:PHAS"),
    "phase_status_is_ok": ("phase_status_is_ok", "SIM:PHAS:STAT", OK_NOK[True], OK_NOK[False]),
    "magnetic_bearing_is_on": ("magnetic_bearing_is_on", "SIM:MB", ON_OFF[True], ON_OFF[False]),
    "magnetic_bearing_status_is_ok": (
        "magnetic_bearing_status_is_ok",
        "SIM:MB:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "drive_is_on": ("drive_is_on", "SIM:DRIVE", ON_OFF[True], ON_OFF[False]),
    "drive_mode_is_start": (
        "drive_mode_is_start",
        "SIM:DRIVE:MODE",
        START_STOP[True],
        START_STOP[False],
    ),
    "drive_l1_current": ("drive_l1_current", "SIM:DRIVE:L1:CURR"),
    "drive_l2_current": ("drive_l2_current", "SIM:DRIVE:L2:CURR"),
    "drive_l3_current": ("drive_l3_current", "SIM:DRIVE:L3:CURR"),
    "drive_direction_is_cw": (
        "drive_direction_is_cw",
        "SIM:DRIVE:DIR",
        CW_CCW[True],
        CW_CCW[False],
    ),
    "drive_temperature": ("drive_temperature", "SIM:DRIVE:TEMP"),
    "phase_outage": ("phase_outage", "SIM:PHAS:OUTAGE"),
    "logging_is_on": ("logging_is_on", "SIM:LOGGING", ON_OFF[True], ON_OFF[False]),
    "dsp_status_is_ok": ("dsp_status_is_ok", "SIM:DSP:STAT", OK_NOK[True], OK_NOK[False]),
    "interlock_er_status_is_ok": (
        "interlock_er_status_is_ok",
        "SIM:INTERLOCK:ER:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "interlock_vacuum_status_is_ok": (
        "interlock_vacuum_status_is_ok",
        "SIM:INTERLOCK:VAC:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "interlock_frequency_monitoring_status_is_ok": (
        "interlock_frequency_monitoring_status_is_ok",
        "SIM:INTERLOCK:FREQMON:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "interlock_magnetic_bearing_amplifier_temperature_status_is_ok": (
        "interlock_magnetic_bearing_amplifier_temperature_status_is_ok",
        "SIM:INTERLOCK:MB:AMP:TEMP:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "interlock_magnetic_bearing_amplifier_current_status_is_ok": (
        "interlock_magnetic_bearing_amplifier_current_status_is_ok",
        "SIM:INTERLOCK:MB:AMP:CURR:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "interlock_drive_amplifier_temperature_status_is_ok": (
        "interlock_drive_amplifier_temperature_status_is_ok",
        "SIM:INTERLOCK:DRIVE:AMP:TEMP:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "interlock_drive_amplifier_current_status_is_ok": (
        "interlock_drive_amplifier_current_status_is_ok",
        "SIM:INTERLOCK:DRIVE:AMP:CURR:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
    "interlock_ups_status_is_ok": (
        "interlock_ups_status_is_ok",
        "SIM:INTERLOCK:UPS:STAT",
        OK_NOK[True],
        OK_NOK[False],
    ),
}


class FzjDigitalDriveFermiChopperTests(unittest.TestCase):
    """
    Tests for the FZJ Digital Drive Fermi Chopper Controller
    """

    def setUp(self):
        """
        Initializes emulator:
            - runs emulator and IOC
            - sets device prefix (IOC name).  Checks for presence of disable PV, otherwise waits for it to be present.
                i.e. halts tests until IOC running
            - sets chopper name (required for all commands and constant in this case)
            - resets the emulator by calling reset command via backdoor.  sets internal values to defaults.
        """

        self._lewis, self._ioc = get_running_lewis_and_ioc("fzj_dd_fermi_chopper", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_wait_time=0.0)

        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_set_on_device("chopper_name", chopper_name)
            self._lewis.backdoor_command(["device", "reset"])

    #   Command definitions:
    def _set_simulated_value(self, parameter, value):
        """
        Sets PV value and backdoor parameter based on lookup from dictionary

            If key has 4 values associated, then refers to a boolean parameter.  Value tested then set accordingly.
            If not, then parameter is either int or float and is set directly.
        Then sets parameter on emulator via backdoor command

        Args:
            parameter: dictionary key to look up values for
            (backdoor parameter, PV name, optional for booleans: (true value, false value))
            value: value to set via backdoor

        Returns:
        """

        simulated_value = SIMULATED_VALUES[parameter]
        if len(simulated_value) == 4:
            backdoor_parameter, pv_name, true_value, false_value = simulated_value
            self._ioc.set_simulated_value(pv_name, true_value if value else false_value)
        else:
            backdoor_parameter, pv_name = simulated_value
            self._ioc.set_simulated_value(pv_name, value)
        self._lewis.backdoor_set_on_device(backdoor_parameter, value)

    def test_GIVEN_frequency_setpoint_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 100
        self._set_simulated_value("frequency_setpoint", expected_value)

        self.ca.assert_that_pv_is("FREQ:SP:RBV", expected_value)
        self.ca.assert_that_pv_alarm_is("FREQ:SP:RBV", self.ca.Alarms.NONE)

    def test_GIVEN_phase_setpoint_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 45.2
        self._set_simulated_value("phase_setpoint", expected_value)

        self.ca.assert_that_pv_is("PHAS:SP:RBV", expected_value)
        self.ca.assert_that_pv_alarm_is("PHAS:SP:RBV", self.ca.Alarms.NONE)

    def test_GIVEN_phase_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("phase_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("PHAS:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("PHAS:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_magnetic_bearing_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("magnetic_bearing_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("MB:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("MB:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_magnetic_bearing_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in ON_OFF.items():
            self._set_simulated_value("magnetic_bearing_is_on", boolean_value)

            self.ca.assert_that_pv_is("MB", expected_value)
            self.ca.assert_that_pv_alarm_is("MB", self.ca.Alarms.NONE)

    def test_GIVEN_drive_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in ON_OFF.items():
            self._set_simulated_value("drive_is_on", boolean_value)

            self.ca.assert_that_pv_is("DRIVE", expected_value)
            self.ca.assert_that_pv_alarm_is("DRIVE", self.ca.Alarms.NONE)

    def test_GIVEN_drive_mode_WHEN_read_all_status_THEN_value_is_as_expected(self):
        for boolean_value, expected_value in START_STOP.items():
            self._set_simulated_value("drive_mode_is_start", boolean_value)

            self.ca.assert_that_pv_is("DRIVE:MODE", expected_value)
            self.ca.assert_that_pv_alarm_is("DRIVE:MODE", self.ca.Alarms.NONE)

    def test_GIVEN_drive_l1_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 9.62
        self._set_simulated_value("drive_l1_current", expected_value)

        self.ca.assert_that_pv_is("DRIVE:L1:CURR", expected_value)
        self.ca.assert_that_pv_alarm_is("DRIVE:L1:CURR", self.ca.Alarms.NONE)

    def test_GIVEN_drive_l2_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 2.74
        self._set_simulated_value("drive_l2_current", expected_value)

        self.ca.assert_that_pv_is("DRIVE:L2:CURR", expected_value)
        self.ca.assert_that_pv_alarm_is("DRIVE:L2:CURR", self.ca.Alarms.NONE)

    def test_GIVEN_drive_l3_current_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 12.48
        self._set_simulated_value("drive_l3_current", expected_value)

        self.ca.assert_that_pv_is("DRIVE:L3:CURR", expected_value)
        self.ca.assert_that_pv_alarm_is("DRIVE:L3:CURR", self.ca.Alarms.NONE)

    def test_GIVEN_drive_direction_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in CW_CCW.items():
            self._set_simulated_value("drive_direction_is_cw", boolean_value)

            self.ca.assert_that_pv_is("DRIVE:DIR", expected_value)
            self.ca.assert_that_pv_alarm_is("DRIVE:DIR", self.ca.Alarms.NONE)

    def test_GIVEN_drive_temperature_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 86.31
        self._set_simulated_value("drive_temperature", expected_value)

        self.ca.assert_that_pv_is("DRIVE:TEMP", expected_value)
        self.ca.assert_that_pv_alarm_is("DRIVE:TEMP", self.ca.Alarms.NONE)

    def test_GIVEN_phase_outage_WHEN_read_all_status_THEN_value_is_as_expected(self):
        expected_value = 354.71
        self._set_simulated_value("phase_outage", expected_value)

        self.ca.assert_that_pv_is("PHAS:OUTAGE", expected_value)
        self.ca.assert_that_pv_alarm_is("PHAS:OUTAGE", self.ca.Alarms.NONE)

    def test_GIVEN_logging_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in ON_OFF.items():
            self._set_simulated_value("logging_is_on", boolean_value)

            self.ca.assert_that_pv_is("LOGGING", expected_value)
            self.ca.assert_that_pv_alarm_is("LOGGING", self.ca.Alarms.NONE)

    def test_GIVEN_dsp_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("dsp_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("DSP:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("DSP:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_interlock_er_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_er_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:ER:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:ER:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_interlock_vacuum_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_vacuum_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:VAC:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:VAC:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_interlock_frequency_monitoring_status_WHEN_read_all_status_THEN_status_is_as_expected(
        self,
    ):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_frequency_monitoring_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:FREQMON:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:FREQMON:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_interlock_magnetic_bearing_amplifier_temperature_status_WHEN_read_all_status_THEN_status_is_as_expected(
        self,
    ):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value(
                "interlock_magnetic_bearing_amplifier_temperature_status_is_ok", boolean_value
            )

            self.ca.assert_that_pv_is("INTERLOCK:MB:AMP:TEMP:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:MB:AMP:TEMP:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_interlock_magnetic_bearing_amplifier_current_status_WHEN_read_all_status_THEN_status_is_as_expected(
        self,
    ):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value(
                "interlock_magnetic_bearing_amplifier_current_status_is_ok", boolean_value
            )

            self.ca.assert_that_pv_is("INTERLOCK:MB:AMP:CURR:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:MB:AMP:CURR:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_interlock_drive_amplifier_temperature_status_WHEN_read_all_status_THEN_status_is_as_expected(
        self,
    ):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value(
                "interlock_drive_amplifier_temperature_status_is_ok", boolean_value
            )

            self.ca.assert_that_pv_is("INTERLOCK:DRIVE:AMP:TEMP:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:DRIVE:AMP:TEMP:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_interlock_drive_amplifier_current_status_WHEN_read_all_status_THEN_status_is_as_expected(
        self,
    ):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value(
                "interlock_drive_amplifier_current_status_is_ok", boolean_value
            )

            self.ca.assert_that_pv_is("INTERLOCK:DRIVE:AMP:CURR:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:DRIVE:AMP:CURR:STAT", self.ca.Alarms.NONE)

    def test_GIVEN_ups_status_WHEN_read_all_status_THEN_status_is_as_expected(self):
        for boolean_value, expected_value in OK_NOK.items():
            self._set_simulated_value("interlock_ups_status_is_ok", boolean_value)

            self.ca.assert_that_pv_is("INTERLOCK:UPS:STAT", expected_value)
            self.ca.assert_that_pv_alarm_is("INTERLOCK:UPS:STAT", self.ca.Alarms.NONE)

    # ***** Test set commands *****

    # Frequency

    def test_GIVEN_drive_mode_is_start_WHEN_frequency_setpoint_is_set_THEN_frequency_reaches_setpoint(
        self,
    ):
        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[True])

        frequency = 600
        self.ca.set_pv_value("FREQ:SP", str(frequency))

        self.ca.assert_that_pv_is_number("FREQ", frequency, timeout=30)
        self.ca.assert_that_pv_alarm_is("FREQ", self.ca.Alarms.NONE)

    def test_GIVEN_drive_mode_is_stop_WHEN_frequency_setpoint_is_set_THEN_frequency_is_zero(self):
        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[False])

        frequency = 600
        self.ca.set_pv_value("FREQ:SP", str(frequency))

        self.ca.assert_that_pv_is_number("FREQ", 0, timeout=30)
        self.ca.assert_that_pv_alarm_is("FREQ", self.ca.Alarms.NONE)

    def test_GIVEN_frequency_setpoint_is_set_WHEN_drive_mode_is_start_THEN_frequency_reaches_setpoint(
        self,
    ):
        frequency = 600
        self.ca.set_pv_value("FREQ:SP", str(frequency))

        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[True])

        self.ca.assert_that_pv_is_number("FREQ", frequency, timeout=30)
        self.ca.assert_that_pv_alarm_is("FREQ", self.ca.Alarms.NONE)

    def test_GIVEN_frequency_setpoint_is_set_WHEN_drive_mode_is_stop_THEN_frequency_is_zero(self):
        frequency = 600
        self.ca.set_pv_value("FREQ:SP", str(frequency))

        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[False])

        self.ca.assert_that_pv_is_number("FREQ", 0, timeout=30)
        self.ca.assert_that_pv_alarm_is("FREQ", self.ca.Alarms.NONE)

    def test_WHEN_frequency_setpoint_is_set_THEN_readback_updates(self):
        frequency = 150
        frequency_as_string = str(frequency)
        self.ca.set_pv_value("FREQ:SP", frequency_as_string)

        self.ca.assert_that_pv_is("FREQ:SP", frequency_as_string)
        self.ca.assert_that_pv_alarm_is("FREQ:SP", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("FREQ:SP:RBV", frequency)
        self.ca.assert_that_pv_alarm_is("FREQ:SP:RBV", self.ca.Alarms.NONE)

    def test_GIVEN_error_WHEN_set_frequency_THEN_error_is_handled(self):
        frequency = 150
        frequency_as_string = str(frequency)
        expected_error = "07;C01NOK;RATIO_SPEED_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_frequency", expected_error)
        self.ca.set_pv_value("FREQ:SP", frequency_as_string)

        self.ca.assert_that_pv_alarm_is("FREQ:SP", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("FREQ:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_frequency_THEN_error_is_cleared(self):
        frequency = 150
        frequency_as_string = str(frequency)
        expected_error = "07;C01NOK;RATIO_SPEED_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_frequency", expected_error)
        self.ca.set_pv_value("FREQ:SP", frequency_as_string)
        self.ca.assert_that_pv_alarm_is("FREQ:SP", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("FREQ:SP:ERROR", expected_error)
        self._lewis.backdoor_set_on_device("error_on_set_frequency", None)

        self.ca.set_pv_value("FREQ:SP", frequency_as_string)

        self.ca.assert_that_pv_is("FREQ:SP:ERROR", "")

    #  Phase

    def test_GIVEN_drive_mode_is_start_WHEN_phase_setpoint_is_set_THEN_phase_reaches_setpoint(self):
        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[True])

        phase = 65.7
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_that_pv_is_number("PHAS", phase, timeout=30)
        self.ca.assert_that_pv_alarm_is("PHAS", self.ca.Alarms.NONE)

    def test_GIVEN_drive_mode_is_stop_WHEN_phase_setpoint_is_set_THEN_phase_is_zero(self):
        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[False])

        phase = 65.7
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_that_pv_is_number("PHAS", 0, timeout=30)
        self.ca.assert_that_pv_alarm_is("PHAS", self.ca.Alarms.NONE)

    def test_GIVEN_phase_setpoint_is_set_WHEN_drive_mode_is_start_THEN_phase_reaches_setpoint(self):
        phase = 65.7
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[True])

        self.ca.assert_that_pv_is_number("PHAS", phase, timeout=30)
        self.ca.assert_that_pv_alarm_is("PHAS", self.ca.Alarms.NONE)

    def test_GIVEN_phase_setpoint_is_set_WHEN_drive_mode_is_stop_THEN_phase_is_zero(self):
        phase = 65.7
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.set_pv_value("DRIVE:MODE:SP", START_STOP[False])

        self.ca.assert_that_pv_is_number("PHAS", 0, timeout=30)
        self.ca.assert_that_pv_alarm_is("PHAS", self.ca.Alarms.NONE)

    def test_WHEN_phase_setpoint_is_set_THEN_readback_updates(self):
        phase = 243.8
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_that_pv_is("PHAS:SP", phase)
        self.ca.assert_that_pv_alarm_is("PHAS:SP", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("PHAS:SP:RBV", phase)
        self.ca.assert_that_pv_alarm_is("PHAS:SP:RBV", self.ca.Alarms.NONE)

    def test_GIVEN_error_WHEN_set_phase_THEN_error_is_handled(self):
        phase = 243.8
        expected_error = "09;CxxNOK;SETPOINT_PHASE_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_phase", expected_error)
        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_that_pv_alarm_is("PHAS:SP", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("PHAS:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_phase_THEN_error_is_cleared(self):
        phase = 243.8
        expected_error = "09;CxxNOK;SETPOINT_PHASE_OUT_OF_RANGE"
        self._lewis.backdoor_set_on_device("error_on_set_phase", expected_error)
        self.ca.set_pv_value("PHAS:SP", phase)
        self.ca.assert_that_pv_alarm_is("PHAS:SP", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("PHAS:SP:ERROR", expected_error)
        self._lewis.backdoor_set_on_device("error_on_set_phase", None)

        self.ca.set_pv_value("PHAS:SP", phase)

        self.ca.assert_that_pv_is("PHAS:SP:ERROR", "")

    # Magnetic Bearing

    def test_WHEN_magnetic_bearing_is_set_THEN_readback_updates(self):
        for magnetic_bearing in [ON_OFF[True], ON_OFF[False]]:
            self.ca.set_pv_value("MB:SP", magnetic_bearing)

            self.ca.assert_that_pv_is("MB:SP", magnetic_bearing)
            self.ca.assert_that_pv_alarm_is("MB:SP", self.ca.Alarms.NONE)
            self.ca.assert_that_pv_is("MB", magnetic_bearing)
            self.ca.assert_that_pv_alarm_is("MB", self.ca.Alarms.NONE)

    def test_GIVEN_error_WHEN_set_magnetic_bearing_is_on_THEN_error_is_handled(self):
        for magnetic_bearing in [ON_OFF[True], ON_OFF[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_magnetic_bearing", expected_error)
            self.ca.set_pv_value("MB:SP", magnetic_bearing)

            self.ca.assert_that_pv_alarm_is("MB:SP", self.ca.Alarms.INVALID)
            self.ca.assert_that_pv_is("MB:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_magnetic_bearing_is_on_THEN_error_is_cleared(self):
        for magnetic_bearing in [ON_OFF[True], ON_OFF[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_magnetic_bearing", expected_error)
            self.ca.set_pv_value("MB:SP", magnetic_bearing)
            self.ca.assert_that_pv_alarm_is("MB:SP", self.ca.Alarms.INVALID)
            self.ca.assert_that_pv_is("MB:SP:ERROR", expected_error)
            self._lewis.backdoor_set_on_device("error_on_set_magnetic_bearing", None)

            self.ca.set_pv_value("MB:SP", magnetic_bearing)

            self.ca.assert_that_pv_is("MB:SP:ERROR", "")

    # Drive

    def test_WHEN_drive_mode_is_set_THEN_readback_updates(self):
        for drive_mode in [START_STOP[True], START_STOP[False]]:
            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)

            self.ca.assert_that_pv_is("DRIVE:MODE:SP", drive_mode)
            self.ca.assert_that_pv_alarm_is("DRIVE:MODE:SP", self.ca.Alarms.NONE)
            self.ca.assert_that_pv_is("DRIVE:MODE", drive_mode)
            self.ca.assert_that_pv_alarm_is("DRIVE:MODE", self.ca.Alarms.NONE)

    def test_GIVEN_error_WHEN_set_drive_mode_is_start_THEN_error_is_handled(self):
        for drive_mode in [START_STOP[True], START_STOP[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_drive_mode", expected_error)
            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)

            self.ca.assert_that_pv_alarm_is("DRIVE:MODE:SP", self.ca.Alarms.INVALID)
            self.ca.assert_that_pv_is("DRIVE:MODE:SP:ERROR", expected_error)

    def test_GIVEN_error_then_no_error_WHEN_set_drive_mode_is_start_THEN_error_is_cleared(self):
        for drive_mode in [START_STOP[True], START_STOP[False]]:
            expected_error = "10;CxxNOK;MAGNETIC_BEARING_NOT_OK"
            self._lewis.backdoor_set_on_device("error_on_set_drive_mode", expected_error)
            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)
            self.ca.assert_that_pv_alarm_is("DRIVE:MODE:SP", self.ca.Alarms.INVALID)
            self.ca.assert_that_pv_is("DRIVE:MODE:SP:ERROR", expected_error)
            self._lewis.backdoor_set_on_device("error_on_set_drive_mode", None)

            self.ca.set_pv_value("DRIVE:MODE:SP", drive_mode)

            self.ca.assert_that_pv_is("DRIVE:MODE:SP:ERROR", "")

    @parameterized.expand(
        [
            ("frequency_setpoint", "FREQ:SP:RBV"),
            ("frequency", "FREQ"),
            ("phase_setpoint", "PHAS:SP:RBV"),
            ("phase", "PHAS"),
            ("phase_status", "PHAS:STAT"),
            ("mag_bear", "MB"),
            ("mag_bear_status", "MB:STAT"),
            ("drive", "DRIVE"),
            ("drive_mode", "DRIVE:MODE"),
            ("drive_l1_current", "DRIVE:L1:CURR"),
            ("drive_l2_current", "DRIVE:L2:CURR"),
            ("drive_l3_current", "DRIVE:L3:CURR"),
            ("drive_direction", "DRIVE:DIR"),
            ("drive_temp", "DRIVE:TEMP"),
            ("phase_outage", "PHAS:OUTAGE"),
            ("logging", "LOGGING"),
            ("dsp_monitoring_status", "DSP:STAT"),
            ("interlock_er_status", "INTERLOCK:ER:STAT"),
            ("interlock_vacuum_status", "INTERLOCK:VAC:STAT"),
            ("interlock_freq_monitoring_status", "INTERLOCK:FREQMON:STAT"),
            ("interlock_mag_bear_amp_temp_status", "INTERLOCK:MB:AMP:TEMP:STAT"),
            ("interlock_mag_bear_amp_curr_status", "INTERLOCK:MB:AMP:CURR:STAT"),
            ("interlock_drive_amp_temp_status", "INTERLOCK:DRIVE:AMP:TEMP:STAT"),
            ("interlock_drive_amp_curr_status", "INTERLOCK:DRIVE:AMP:CURR:STAT"),
            ("interlock_ups_status", "INTERLOCK:UPS:STAT"),
        ]
    )
    def test_GIVEN_device_is_not_communicating_WHEN_read_status_THEN_value_has_error(self, _, pv):
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE, timeout=30)

        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID, timeout=30)

        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE, timeout=30)
