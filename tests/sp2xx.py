import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, unstable_test

DEVICE_PREFIX = "SP2XX_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SP2XX"),
        "macros": {},
        "emulator": "sp2xx",
    }
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


# Useful commands to help run tests
###################################


def _reset_device():
    """Reset the sp2xx device"""
    lewis, ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
    ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)

    _stop_running(ca)
    ca.assert_that_pv_is("STATUS", "Stopped")

    lewis.backdoor_run_function_on_device("clear_last_error")
    ca.process_pv("ERROR")
    ca.assert_that_pv_is("ERROR", "No error")

    ca.assert_setting_setpoint_sets_readback("Infusion", "MODE")

    ca.assert_that_pv_is("NA", "No error")

    return lewis, ioc, ca


def _start_running(ca):
    """
    Start device running
    Args:
        ca: channel access object
    """
    ca.set_pv_value("RUN:SP", 1)


def _stop_running(ca):
    """
    Stop device running
    Args:
        ca: channel access object
    """

    ca.set_pv_value("STOP:SP", 1)


# Tests in various classes
##########################


class RunCommandTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    def test_that_GIVEN_an_initialized_pump_THEN_it_is_stopped(self):
        # Then:
        self.ca.assert_that_pv_is("STATUS", "Stopped")

    def test_that_GIVEN_a_pump_in_infusion_mode_which_is_not_running_THEN_the_pump_starts_running_(
        self,
    ):
        # When
        _start_running(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Infusion")

    def test_that_GIVEN_the_pump_is_running_infusion_mode_WHEN_told_to_run_THEN_the_pump_is_still_running_in_infusion_mode(
        self,
    ):
        # Given
        _start_running(self.ca)
        self.ca.assert_that_pv_is("STATUS", "Infusion")

        # When
        _start_running(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Infusion")


class StopCommandTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    def test_that_GIVEN_a_running_pump_THEN_the_pump_stops(self):
        # Given
        _start_running(self.ca)
        self.ca.assert_that_pv_is("STATUS", "Infusion")

        # When:
        _stop_running(self.ca)

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Stopped")

    def test_that_GIVEN_a_stopped_pump_THEN_the_pump_remains_stopped(self):
        # Given
        _stop_running(self.ca)

        # When:
        _stop_running(self.ca)

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


errors = [
    no_error,
    comms_error,
    stall_error,
    comms_stall_error,
    ser_overrun_error,
    ser_and_overrun_error,
    stall_and_ser_overrun_error,
    stall_ser_error_and_overrun,
]


class ErrorTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    @skip_if_recsim("Recsim does not do errors")
    def test_that_GIVEN_an_initialized_pump_THEN_the_device_has_no_error(self):
        # Then:
        self.ca.process_pv("ERROR")
        self.ca.assert_that_pv_is("ERROR", "No error")
        self.ca.assert_that_pv_alarm_is("ERROR", ChannelAccess.Alarms.NONE)

    @parameterized.expand([(error.name, error) for error in errors[1:]])
    @skip_if_recsim("Recsim does not do errors")
    def test_that_GIVEN_a_device_with_an_error_WHEN_trying_to_start_the_device_THEN_the_error_pv_is_updated_and_device_is_stopped(
        self, _, error
    ):
        # Given:
        self._lewis.backdoor_run_function_on_device(
            "throw_error_via_the_backdoor", [error.name, error.value, error.alarm_severity]
        )

        # When:
        _start_running(self.ca)

        # Then:
        self.ca.assert_that_pv_is("ERROR", error.name)
        self.ca.assert_that_pv_alarm_is("ERROR", error.alarm_severity)
        self.ca.assert_that_pv_is("STATUS", "Stopped")


class ModeSwitchingTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    MODES = ["Infusion/Withdrawal", "Withdrawal/Infusion", "Infusion", "Withdrawal", "Continuous"]

    def test_that_GIVEN_an_initialized_pump_THEN_the_mode_is_set_to_infusing(self):
        # Then:
        self.ca.assert_that_pv_is("MODE", "Infusion")

    @parameterized.expand(MODES)
    def test_that_GIVEN_an__pump_in_one_mode_WHEN_a_different_mode_is_set_THEN_the_mode_is_read(
        self, mode
    ):
        self.ca.assert_setting_setpoint_sets_readback(mode, "MODE")


class DirectionTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    @parameterized.expand(["Infusion", "Infusion/Withdrawal", "Continuous"])
    def test_that_WHEN_a_device_in_set_in_an_infusion_like_mode_THEN_the_devices_direction_is_infusion(
        self, mode
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback(mode, "MODE")

        # Then:
        self.ca.assert_that_pv_is("DIRECTION", "Infusion")

    @parameterized.expand(["Withdrawal", "Withdrawal/Infusion"])
    def test_that_WHEN_a_device_in_set_in_an_withdrawal_like_mode_THEN_the_devices_direction_is_withdrawal(
        self, mode
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback(mode, "MODE")

        # Then:
        self.ca.assert_that_pv_is("DIRECTION", "Withdrawal")

    @parameterized.expand([("Infusion", "Withdrawal"), ("Withdrawal", "Infusion")])
    def test_that_GIVEN_a_running_device_WHEN_the_device_is_told_to_reverse_the_direction_THEN_the_direction_is_reversed_an_NA_has_not_been_triggered(
        self, inital_mode, expected_direction
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback(inital_mode, "MODE")

        self.ca.assert_that_pv_is("DIRECTION", inital_mode)

        _start_running(self.ca)
        self.ca.assert_that_pv_is("STATUS", inital_mode)

        # When:
        self.ca.set_pv_value("DIRECTION:REV", 1)

        # Then:
        self.ca.assert_that_pv_is("DIRECTION", expected_direction)
        self.ca.assert_that_pv_is("NA", "No error")

    @parameterized.expand(
        [
            ("Infusion", "Infusion"),
            ("Withdrawal", "Withdrawal"),
            ("Infusion/Withdrawal", "Infusion"),
            ("Withdrawal/Infusion", "Withdrawal"),
            ("Continuous", "Infusion"),
        ]
    )
    @skip_if_recsim("Can not test NA in rec sim")
    def test_that_GIVEN_a_device_stopped_device_WHEN_the_dir_rev_is_queried_THEN_the_devices_direction_has_not_changed_and_NA_is_triggered(
        self, initial_mode, expected_direction
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback(initial_mode, "MODE")
        self.ca.assert_that_pv_is("DIRECTION", expected_direction)

        _stop_running(self.ca)
        self.ca.assert_that_pv_is("STATUS", "Stopped")

        # When:
        self.ca.set_pv_value("DIRECTION:REV", 1)

        # Then:
        self.ca.assert_that_pv_is("DIRECTION", expected_direction)
        self.ca.assert_that_pv_is("NA", "Can't run command")

    @parameterized.expand(
        [
            ("Infusion/Withdrawal", "Infusion"),
            ("Withdrawal/Infusion", "Withdrawal"),
            ("Continuous", "Infusion"),
        ]
    )
    @skip_if_recsim("Can not test NA in rec sim")
    def test_that_GIVEN_a_device_running_not_in_infusion_or_withdrawal_mode_WHEN_the_direction_is_reverse_THEN_the_devices_direction_has_not_changed_and_NA_is_triggered(
        self, mode, expected_direction
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback(mode, "MODE")

        _start_running(self.ca)
        self.ca.assert_that_pv_is("DIRECTION", expected_direction)
        self.ca.assert_that_pv_is("STATUS", expected_direction)

        # When:
        self.ca.set_pv_value("DIRECTION:REV", 1)

        # Then:
        self.ca.assert_that_pv_is("DIRECTION", expected_direction)
        self.ca.assert_that_pv_is("NA", "Can't run command")


class NATests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    @skip_if_recsim("NA can only be set through complicated logic not in recsim")
    def test_that_GIVEN_a_device_in_withdrawal_mode_WHEN_starting_the_device_THEN_NA_is_not_triggered(
        self,
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback("Withdrawal", "MODE")

        # When:
        _start_running(self.ca)

        # Then:
        self.ca.assert_that_pv_is("NA", "No error")

    @skip_if_recsim("NA can only be set through complicated logic not in recsim")
    def test_that_GIVEN_a_device_in_withdrawal_mode_with_NA_triggered_WHEN_starting_the_device_THEN_NA_is_reset(
        self,
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback("Withdrawal", "MODE")

        self.ca.set_pv_value("NA", 0, sleep_after_set=0)
        self.ca.assert_that_pv_is("NA", "Can't run command")

        # When:
        _start_running(self.ca)
        self.ca.assert_that_pv_is("STATUS", "Withdrawal")

        # Then:
        self.ca.assert_that_pv_is("NA", "No error")

    @skip_if_recsim("NA can only be set through complicated logic not in recsim")
    def test_that_GIVEN_a_device_in_infusion_mode_with_NA_triggered_WHEN_starting_the_device_THEN_NA_is_reset(
        self,
    ):
        # Given:
        self.ca.assert_setting_setpoint_sets_readback("Infusion", "MODE")

        self.ca.set_pv_value("NA", 0, sleep_after_set=0)
        self.ca.assert_that_pv_is("NA", "Can't run command")

        # When:
        _start_running(self.ca)
        self.ca.assert_that_pv_is("STATUS", "Infusion", timeout=15)

        # Then:
        self.ca.assert_that_pv_is("NA", "No error")


class DiameterTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    @parameterized.expand(
        [("10.05", 10.05), ("01.45", 01.45), ("00.0100000000", 00.0100000000), ("99.87", 99.87)]
    )
    def test_that_WHEN_the_diameter_is_set_THEN_it_is_set(self, _, value):
        # Then:
        self.ca.assert_setting_setpoint_sets_readback(value, "DIAMETER", "DIAMETER:SP")


class VolumeTests(unittest.TestCase):
    def setUp(self):
        # Given
        self._lewis, self._ioc, self.ca = _reset_device()

    @parameterized.expand(
        [
            (123, "ml"),
            (123, "ul"),
            (1, "ml"),
            (9999, "ml"),
            (99.87, "ml"),
            (123.7, "ml"),
            (1.237, "ml"),
        ]
    )
    def test_GIVEN_value_then_units_set_volume_infusion_WHEN_set_to_various_THEN_read_back_is_value(
        self, value, units
    ):
        self.ca.set_pv_value("VOL:INF:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "VOL:INF", "VOL:INF:SP")
        self.ca.assert_that_pv_is("VOL:INF:UNITS", units)
        self.ca.assert_that_pv_is("VOL:INF.EGU", units)
        self.ca.assert_that_pv_is("VOL:INF:UNITS:SP", units)
        self.ca.assert_that_pv_is("VOL:INF:SP.EGU", units)

    @skip_if_recsim("Can not set units in device via back door")
    def test_GIVEN_infusion_unit_set_in_device_WHEN_nothing_THEN_units_are_set_on_readback(self):
        ul = "ul"
        self._lewis.backdoor_set_on_device("infusion_volume_units", ul)
        self.ca.assert_that_pv_is("VOL:INF:UNITS", ul)
        self.ca.assert_that_pv_is("VOL:INF.EGU", ul)

        ml = "ml"
        self._lewis.backdoor_set_on_device("infusion_volume_units", ml)
        self.ca.assert_that_pv_is("VOL:INF:UNITS", ml)
        self.ca.assert_that_pv_is("VOL:INF.EGU", ml)

    @parameterized.expand(
        [
            (123, "ml"),
            (123, "ul"),
            (1, "ml"),
            (9999, "ml"),
            (99.87, "ml"),
            (123.7, "ml"),
            (1.237, "ml"),
        ]
    )
    def test_GIVEN_value_then_units_set_volume_withdraw_WHEN_set_to_various_THEN_read_back_is_value(
        self, value, units
    ):
        self.ca.set_pv_value("VOL:WDR:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "VOL:WDR", "VOL:WDR:SP")
        self.ca.assert_that_pv_is("VOL:WDR:UNITS", units)
        self.ca.assert_that_pv_is("VOL:WDR.EGU", units)
        self.ca.assert_that_pv_is("VOL:WDR:UNITS:SP", units)
        self.ca.assert_that_pv_is("VOL:WDR:SP.EGU", units)

    @skip_if_recsim("Can not set backdoor in rec sim mode")
    def test_GIVEN_withdrawal_unit_set_in_device_WHEN_nothing_THEN_units_are_set_on_readback(self):
        ul = "ul"
        self._lewis.backdoor_set_on_device("withdrawal_volume_units", ul)
        self.ca.assert_that_pv_is("VOL:WDR:UNITS", ul)
        self.ca.assert_that_pv_is("VOL:WDR.EGU", ul)

        ml = "ml"
        self._lewis.backdoor_set_on_device("withdrawal_volume_units", ml)
        self.ca.assert_that_pv_is("VOL:WDR:UNITS", ml)
        self.ca.assert_that_pv_is("VOL:WDR.EGU", ml)

    @parameterized.expand(
        [
            (123, "ml/m"),
            (123, "ul/m"),
            (1, "ml/h"),
            (9999, "ul/h"),
            (99.87, "ml/h"),
            (123.7, "ml/h"),
            (1.237, "ml/h"),
        ]
    )
    def test_GIVEN_set_infusion_rate_and_units_WHEN_set_to_various_THEN_read_back_is_value_with_units(
        self, value, units
    ):
        self.ca.set_pv_value("RATE:INF:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "RATE:INF", "RATE:INF:SP")
        self.ca.assert_that_pv_is("RATE:INF:UNITS", units)
        self.ca.assert_that_pv_is("RATE:INF.EGU", units)
        self.ca.assert_that_pv_is("RATE:INF:UNITS:SP", units)
        self.ca.assert_that_pv_is("RATE:INF:SP.EGU", units)

    @parameterized.expand(
        [
            (123, "ml/m"),
            (123, "ul/m"),
            (1, "ml/h"),
            (9999, "ul/h"),
            (99.87, "ml/h"),
            (123.7, "ml/h"),
            (1.237, "ml/h"),
        ]
    )
    def test_GIVEN_set_withdrawal_rate_and_units_WHEN_set_to_various_THEN_read_back_is_value_with_units(
        self, value, units
    ):
        self.ca.set_pv_value("RATE:WDR:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "RATE:WDR", "RATE:WDR:SP")
        self.ca.assert_that_pv_is("RATE:WDR:UNITS", units)
        self.ca.assert_that_pv_is("RATE:WDR.EGU", units)
        self.ca.assert_that_pv_is("RATE:WDR:UNITS:SP", units)
        self.ca.assert_that_pv_is("RATE:WDR:SP.EGU", units)
