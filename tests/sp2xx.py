import unittest
from parameterized import parameterized
import re
from enum import Enum
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


class LastError(Enum):
    No_error = 0
    Communication_error = 1
    Stall = 2
    Communication_error_and_stall = 3
    Serial_overrun = 4
    Serial_error_and_overrun = 5
    Stall_and_serial_overrun = 6
    Stall_and_serial_error_and_overrun = 7


TEST_MODES = [TestModes.DEVSIM] # TestModes.RECSIM,


class RunCommandTests(unittest.TestCase):
    """
    Tests for the Sp2XX IOC run command.
    """
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("stop_device")
        self._reset_device()

    def tearDown(self):
        self._reset_device()

    def _start_running(self):
        self._lewis.backdoor_run_function_on_device("start_device")

    def _reset_device(self):
        self._lewis.backdoor_run_function_on_device("stop_device")
        self._lewis.backdoor_run_function_on_device("clear_last_error")

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

    def tearDown(self):
        self._reset_device()

    def _start_running(self):
        self._lewis.backdoor_run_function_on_device("start_device")
        self.ca.set_pv_value("RUN:SP", 1)

    def _stop_running(self):
        self._lewis.backdoor_run_function_on_device("stop_device")
        self.ca.set_pv_value("STOP:SP", 1)

    def _reset_device(self):
        self._stop_running()
        self._lewis.backdoor_run_function_on_device("clear_last_error")

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


class ErrorTests(unittest.TestCase):
    """
    Tests for the Sp2XX IOC stop command.
    """
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_device()

    def tearDown(self):
        self._reset_device()

    def _start_running(self):
        self._lewis.backdoor_run_function_on_device("start_device")

    def _stop_running(self):
        self._lewis.backdoor_run_function_on_device("stop_device")

    def _reset_device(self):
        self._lewis.backdoor_run_function_on_device("stop_device")
        self._lewis.backdoor_run_function_on_device("clear_last_error")

    def test_that_GIVEN_an_initialized_pump_THEN_the_device_has_no_error(self):
        # Then:
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")
        self.ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_NONE)

    @parameterized.expand([(error_type.name, error_type) for error_type in LastError])
    def test_that_GIVEN_a_device_with_an_error_WHEN_trying_to_start_the_device_THEN_the_error_pv_is_updated(self, _, error_type):
        # Given:
        self._lewis.backdoor_run_function_on_device("throw_error", [error_type.value])

        # When:
        self._start_running()

        # Then:
        if error_type.value == 7:
            self.ca.assert_that_pv_is("ERROR", "Stall, serial error and overrun")
            self.ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_INVALID)
        else:
            expected = re.sub("_", " ", error_type.name)
            self.ca.assert_that_pv_is("ERROR", expected)
            self.ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_INVALID)
