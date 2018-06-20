import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "SP2XX_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SP2XX"),
        "macros": {},
        "emulator": "sp2xx",
        "emulator_protocol": "stream"
    }
]


TEST_MODES = [TestModes.DEVSIM] # TestModes.RECSIM,


class RunCommandTests(unittest.TestCase):
    """
    Tests for the Sp2XX IOC run command.
    """
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_device()

    def _reset_device(self):
        self._lewis.backdoor_run_function_on_device("clear_last_error")
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")

        self._stop_running()
        self.ca.assert_that_pv_is("STATUS", "Stopped")

        self.ca.set_pv_value("MODE:SP", "i")
        self.ca.assert_that_pv_is("MODE", "Infusion")

    def _start_running(self):
        self.ca.set_pv_value("RUN:SP", 1)

    def _stop_running(self):
        self.ca.set_pv_value("STOP:SP", 1)

    def test_that_GIVEN_an_initialized_pump_THEN_it_is_stopped(self):
        # Then:
        self.ca.assert_that_pv_is("STATUS", "Stopped")

    def test_that_GIVEN_a_pump_in_infusion_mode_which_is_not_running_THEN_the_pump_starts_running_(self):
        # When
        self._start_running()

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Infusing")

    def test_that_GIVEN_the_pump_is_running_infusion_mode_WHEN_told_to_run_THEN_the_pump_is_still_running_in_infusion_mode(self):
        # Given
        self._start_running()
        self.ca.assert_that_pv_is("STATUS", "Infusing")

        # When
        self._start_running()

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Infusing")


class StopCommandTests(unittest.TestCase):
    """
    Tests for the Sp2XX IOC stop command.
    """
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_device()

    def _reset_device(self):
        self._lewis.backdoor_run_function_on_device("clear_last_error")
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")

        self._stop_running()
        self.ca.assert_that_pv_is("STATUS", "Stopped")

        self.ca.set_pv_value("MODE:SP", "i")
        self.ca.assert_that_pv_is("MODE", "Infusion")

    def _start_running(self):
        self.ca.set_pv_value("RUN:SP", 1)

    def _stop_running(self):
        self.ca.set_pv_value("STOP:SP", 1)

    def test_that_GIVEN_a_running_pump_THEN_the_pump_stops(self):
        # Given
        self._start_running()
        self.ca.assert_that_pv_is("STATUS", "Infusing")

        # When:
        self._stop_running()

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Stopped")

    def test_that_GIVEN_a_stopped_pump_THEN_the_pump_remains_stopped(self):
        # Given
        self._stop_running()

        # When:
        self._stop_running()

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Stopped")


class ErrorType(object):
    """
    Error Type.

    Attributes:
        name: String name of the error
        value: integer value of the error
        alarm_severity: Alarm severity of the error
    """
    def __init__(self, name, value, alarm_severity):
        self.name = name
        self.value = value
        self.alarm_severity = alarm_severity


no_error = ErrorType("No error", 0, "NO_ALARM")
comms_error = ErrorType("Comms error", 1, "MAJOR")
stall_error = ErrorType("Stall", 2, "MAJOR")
comms_stall_error = ErrorType("Comms error and stall", 3, "MAJOR")
ser_overrun_error = ErrorType("Serial overrun", 4, "MAJOR")
ser_and_overrun_error = ErrorType("Serial error and overrun", 5, "MAJOR")
stall_and_ser_overrun_error = ErrorType("Stall and serial overrun", 6, "MAJOR")
stall_ser_error_and_overrun = ErrorType("Stall ser err and overun", 7, "MAJOR")


errors = [no_error, comms_error, stall_error, comms_stall_error, ser_overrun_error, ser_and_overrun_error,
          stall_and_ser_overrun_error, stall_ser_error_and_overrun]


class ErrorTests(unittest.TestCase):
    """
    Tests for the Sp2XX IOC stop command.
    """
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_device()

    def _reset_device(self):
        self._lewis.backdoor_run_function_on_device("clear_last_error")
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")

        self._stop_running()
        self.ca.assert_that_pv_is("STATUS", "Stopped")

        self.ca.set_pv_value("MODE:SP", "i")
        self.ca.assert_that_pv_is("MODE", "Infusion")

    def _start_running(self):
        self.ca.set_pv_value("RUN:SP", 1)

    def _stop_running(self):
        self.ca.set_pv_value("STOP:SP", 1)

    def test_that_GIVEN_an_initialized_pump_THEN_the_device_has_no_error(self):
        # Then:
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")
        self.ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_NONE)

    @parameterized.expand([(error.name, error) for error in errors[1:]])
    def test_that_GIVEN_a_device_with_an_error_WHEN_trying_to_start_the_device_THEN_the_error_pv_is_updated_and_device_is_stopped(self, _, error):
        # Given:
        self._lewis.backdoor_run_function_on_device("throw_error_via_the_backdoor",
                                                    [error.name, error.value, error.alarm_severity])

        # When:
        self._start_running()

        # Then:
        self.ca.assert_that_pv_is("ERROR", error.name)
        self.ca.assert_pv_alarm_is("ERROR", error.alarm_severity)
        self.ca.assert_that_pv_is("STATUS", "Stopped")


class Mode(object):
    """
    Operation mode for the device.

    Attributes:
        set_symbol (string): Symbol for setting the mode
        response (string): Response to a query for the mode.
        name: Description of the mode.
    """
    def __init__(self, set_symbol, response, name):
        self.set_symbol = set_symbol
        self.response = response
        self.name = name


infusion = Mode("i", "I", "Infusion")
withdrawal = Mode("w", "W", "Withdrawal")
infusion_withdrawal = Mode("i/w", "I/W", "Infusion/Withdrawal")
withdrawal_infusion = Mode("w/i", "W/I", "Withdrawal/Infusion")
continuous = Mode("con", "CON", "Continuous")

MODES = {
    "i/w": infusion_withdrawal,
    "w/i": withdrawal_infusion,
    "i": infusion,
    "w": withdrawal,
    "con": continuous
}


class ModeSwitchingTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_device()

    def _reset_device(self):
        self._stop_running()
        self.ca.assert_that_pv_is("STATUS", "Stopped")

        self._lewis.backdoor_run_function_on_device("clear_last_error")
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")

        self.ca.set_pv_value("MODE:SP", "i")
        self.ca.assert_that_pv_is("MODE", "Infusion")

    def _start_running(self):
        self.ca.set_pv_value("RUN:SP", 1)

    def _stop_running(self):
        self.ca.set_pv_value("STOP:SP", 1)

    def test_that_GIVEN_an_initialized_pump_THEN_the_mode_is_set_to_infusing(self):
        # Then:
        self.ca.assert_that_pv_is("MODE", "Infusion")

    @parameterized.expand([(mode.name, mode) for mode in MODES.values()])
    def test_that_GIVEN_an__pump_in_one_mode_WHEN_a_different_mode_is_set_THEN_the_mode_is_read(self, _, mode):
        # When:
        self.ca.set_pv_value("MODE:SP", mode.set_symbol)

        # Then:
        self.ca.assert_that_pv_is("MODE", mode.name)


class DirectionTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_device()

    def _reset_device(self):
        self._stop_running()
        self.ca.assert_that_pv_is("STATUS", "Stopped")

        self._lewis.backdoor_run_function_on_device("clear_last_error")
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")

        self.ca.set_pv_value("MODE:SP", "i")
        self.ca.assert_that_pv_is("MODE", "Infusion")

    def _start_running(self):
        self.ca.set_pv_value("RUN:SP", 1)

    def _stop_running(self):
        self.ca.set_pv_value("STOP:SP", 1)

    def test_that_GIVEN_a_device_in_infusion_mode_THEN_the_devices_direction_is_infusing(self):
        # Given:
        self._lewis.backdoor_run_function_on_device("set_direction_via_the_backdoor", ["I"])

        # Then:
        self.ca.assert_that_pv_is("DIRECTION", "Infusion")



