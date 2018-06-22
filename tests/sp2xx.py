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


# class RunCommandTests(unittest.TestCase):
#     """
#     Tests for the Sp2XX IOC run command.
#     """
#     def setUp(self):
#         # Given
#         self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
#         self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
#         self._reset_device()
#
#     def _reset_device(self):
#         self._lewis.backdoor_run_function_on_device("clear_last_error")
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         self.ca.set_pv_value("MODE:SP", "i")
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#     def _start_running(self):
#         self.ca.set_pv_value("RUN:SP", 1)
#
#     def _stop_running(self):
#         self.ca.set_pv_value("STOP:SP", 1)
#
#     def test_that_GIVEN_an_initialized_pump_THEN_it_is_stopped(self):
#         # Then:
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#     def test_that_GIVEN_a_pump_in_infusion_mode_which_is_not_running_THEN_the_pump_starts_running_(self):
#         # When
#         self._start_running()
#
#         # Then:
#         self.ca.assert_that_pv_is("STATUS", "Infusion")
#
#     def test_that_GIVEN_the_pump_is_running_infusion_mode_WHEN_told_to_run_THEN_the_pump_is_still_running_in_infusion_mode(self):
#         # Given
#         self._start_running()
#         self.ca.assert_that_pv_is("STATUS", "Infusion")
#
#         # When
#         self._start_running()
#
#         # Then:
#         self.ca.assert_that_pv_is("STATUS", "Infusion")
#
#
# class StopCommandTests(unittest.TestCase):
#     """
#     Tests for the Sp2XX IOC stop command.
#     """
#     def setUp(self):
#         # Given
#         self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
#         self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
#         self._reset_device()
#
#     def _reset_device(self):
#         self._lewis.backdoor_run_function_on_device("clear_last_error")
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         self.ca.set_pv_value("MODE:SP", "i")
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#     def _start_running(self):
#         self.ca.set_pv_value("RUN:SP", 1)
#
#     def _stop_running(self):
#         self.ca.set_pv_value("STOP:SP", 1)
#
#     def test_that_GIVEN_a_running_pump_THEN_the_pump_stops(self):
#         # Given
#         self._start_running()
#         self.ca.assert_that_pv_is("STATUS", "Infusion")
#
#         # When:
#         self._stop_running()
#
#         # Then:
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#     def test_that_GIVEN_a_stopped_pump_THEN_the_pump_remains_stopped(self):
#         # Given
#         self._stop_running()
#
#         # When:
#         self._stop_running()
#
#         # Then:
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#
# class ErrorType(object):
#     """
#     Error Type.
#
#     Attributes:
#         name: String name of the error
#         value: integer value of the error
#         alarm_severity: Alarm severity of the error
#     """
#     def __init__(self, name, value, alarm_severity):
#         self.name = name
#         self.value = value
#         self.alarm_severity = alarm_severity
#
#
# no_error = ErrorType("No error", 0, "NO_ALARM")
# comms_error = ErrorType("Comms error", 1, "MAJOR")
# stall_error = ErrorType("Stall", 2, "MAJOR")
# comms_stall_error = ErrorType("Comms error and stall", 3, "MAJOR")
# ser_overrun_error = ErrorType("Serial overrun", 4, "MAJOR")
# ser_and_overrun_error = ErrorType("Serial error and overrun", 5, "MAJOR")
# stall_and_ser_overrun_error = ErrorType("Stall and serial overrun", 6, "MAJOR")
# stall_ser_error_and_overrun = ErrorType("Stall ser err and overun", 7, "MAJOR")
#
#
# errors = [no_error, comms_error, stall_error, comms_stall_error, ser_overrun_error, ser_and_overrun_error,
#           stall_and_ser_overrun_error, stall_ser_error_and_overrun]
#
#
# class ErrorTests(unittest.TestCase):
#     """
#     Tests for the Sp2XX IOC stop command.
#     """
#     def setUp(self):
#         # Given
#         self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
#         self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
#         self._reset_device()
#
#     def _reset_device(self):
#         self._lewis.backdoor_run_function_on_device("clear_last_error")
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         self.ca.set_pv_value("MODE:SP", "i")
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#     def _start_running(self):
#         self.ca.set_pv_value("RUN:SP", 1)
#
#     def _stop_running(self):
#         self.ca.set_pv_value("STOP:SP", 1)
#
#     def test_that_GIVEN_an_initialized_pump_THEN_the_device_has_no_error(self):
#         # Then:
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#         self.ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_NONE)
#
#     @parameterized.expand([(error.name, error) for error in errors[1:]])
#     def test_that_GIVEN_a_device_with_an_error_WHEN_trying_to_start_the_device_THEN_the_error_pv_is_updated_and_device_is_stopped(self, _, error):
#         # Given:
#         self._lewis.backdoor_run_function_on_device("throw_error_via_the_backdoor",
#                                                     [error.name, error.value, error.alarm_severity])
#
#         # When:
#         self._start_running()
#
#         # Then:
#         self.ca.assert_that_pv_is("ERROR", error.name)
#         self.ca.assert_pv_alarm_is("ERROR", error.alarm_severity)
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#
# class Mode(object):
#     """
#     Operation mode for the device.
#
#     Attributes:
#         set_symbol (string): Symbol for setting the mode
#         response (string): Response to a query for the mode.
#         name: Description of the mode.
#     """
#     def __init__(self, set_symbol, response, name):
#         self.set_symbol = set_symbol
#         self.response = response
#         self.name = name
#
#
# infusion = Mode("i", "I", "Infusion")
# withdrawal = Mode("w", "W", "Withdrawal")
# infusion_withdrawal = Mode("i/w", "I/W", "Infusion/Withdrawal")
# withdrawal_infusion = Mode("w/i", "W/I", "Withdrawal/Infusion")
# continuous = Mode("con", "CON", "Continuous")
#
# MODES = {
#     "i/w": infusion_withdrawal,
#     "w/i": withdrawal_infusion,
#     "i": infusion,
#     "w": withdrawal,
#     "con": continuous
# }
#
#
# class ModeSwitchingTests(unittest.TestCase):
#     def setUp(self):
#         # Given
#         self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
#         self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
#         self._reset_device()
#
#     def _reset_device(self):
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         self._lewis.backdoor_run_function_on_device("clear_last_error")
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#
#         self.ca.set_pv_value("MODE:SP", "i")
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#     def _start_running(self):
#         self.ca.set_pv_value("RUN:SP", 1)
#
#     def _stop_running(self):
#         self.ca.set_pv_value("STOP:SP", 1)
#
#     def test_that_GIVEN_an_initialized_pump_THEN_the_mode_is_set_to_infusing(self):
#         # Then:
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#     @parameterized.expand([(mode.name, mode) for mode in MODES.values()])
#     def test_that_GIVEN_an__pump_in_one_mode_WHEN_a_different_mode_is_set_THEN_the_mode_is_read(self, _, mode):
#         # When:
#         self.ca.set_pv_value("MODE:SP", mode.set_symbol)
#
#         # Then:
#         self.ca.assert_that_pv_is("MODE", mode.name)
#
#
# class DirectionTests(unittest.TestCase):
#     def setUp(self):
#         # Given
#         self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
#         self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
#         self._reset_device()
#
#     def _reset_device(self):
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         self._lewis.backdoor_run_function_on_device("clear_last_error")
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#
#         self.ca.set_pv_value("MODE:SP", "i")
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#     def _start_running(self):
#         self.ca.set_pv_value("RUN:SP", 1)
#
#     def _stop_running(self):
#         self.ca.set_pv_value("STOP:SP", 1)
#
#     @parameterized.expand(
#         [("infusion", "i", "Infusion"),
#          ("infusion_withdrawal", "i/w", "Infusion/Withdrawal"),
#          ("continuous", "con", "Continuous")])
#     def test_that_WHEN_a_device_in_set_in_an_infusion_like_mode_THEN_the_devices_direction_is_infusion(self, _, mode_symbol, mode_name):
#         # Given:
#         self.ca.set_pv_value("MODE:SP", mode_symbol)
#         self.ca.assert_that_pv_is("MODE", mode_name)
#
#         # Then:
#         self.ca.assert_that_pv_is("DIRECTION", "Infusion")
#
#     @parameterized.expand([
#         ("infusion", "w", "Withdrawal"),
#         ("infusion_withdrawal", "w/i", "Withdrawal/Infusion")])
#     def test_that_WHEN_a_device_in_set_in_an_withdrawal_like_mode_THEN_the_devices_direction_is_withdrawal(self, _, mode_symbol, mode_name):
#         # Given:
#         self.ca.set_pv_value("MODE:SP", mode_symbol)
#         self.ca.assert_that_pv_is("MODE", mode_name)
#
#         # Then:
#         self.ca.assert_that_pv_is("DIRECTION", "Withdrawal")
#
#     @parameterized.expand([("infusion", "i", "Infusion", "Withdrawal"), ("withdrawal", "w", "Withdrawal", "Infusion")])
#     def test_that_GIVEN_a_running_device_WHEN_the_device_is_told_to_reverse_the_direction_THEN_the_direction_is_reversed_an_NA_has_not_been_triggered(self, _, mode_symbol, mode_name, expected_direction):
#         # Given:
#         self.ca.set_pv_value("MODE:SP", mode_symbol)
#         self.ca.assert_that_pv_is("MODE", mode_name)
#
#         self.ca.assert_that_pv_is("DIRECTION", mode_name)
#
#         self._start_running()
#         self.ca.assert_that_pv_is("STATUS", mode_name)
#
#         # When:
#         self.ca.set_pv_value("DIRECTION:REV", 1)
#
#         # Then:
#         self.ca.assert_that_pv_is("DIRECTION", expected_direction)
#         self.ca.assert_that_pv_is("NA", "")
#
#     @parameterized.expand([
#         ("infusion", "i", "Infusion", "Infusion"),
#         ("withdrawal", "w", "Withdrawal", "Withdrawal"),
#         ("infusion_withdrawal", "i/w", "Infusion/Withdrawal", "Infusion"),
#         ("withdrawal_infusion", "w/i", "Withdrawal/Infusion", "Withdrawal"),
#         ("continuous", "con", "Continuous", "Infusion")
#         ])
#     def test_that_GIVEN_a_device_stopped_device_WHEN_the_dir_rev_is_queried_THEN_the_devices_direction_has_not_changed_and_NA_is_triggered(self, _, mode_symbol, mode_name, expected_direction):
#         # Given:
#         self.ca.set_pv_value("MODE:SP", mode_symbol)
#         self.ca.assert_that_pv_is("MODE", mode_name)
#         self.ca.assert_that_pv_is("DIRECTION", expected_direction)
#
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         # When:
#         self.ca.set_pv_value("DIRECTION:REV", 1)
#
#         # Then:
#         self.ca.assert_that_pv_is("DIRECTION", expected_direction)
#         self.ca.assert_that_pv_is("NA", "Can't run command")
#
#
#     @parameterized.expand([
#         ("infusion_withdrawal", "i/w", "Infusion/Withdrawal", "Infusion"),
#         ("withdrawal_infusion", "w/i", "Withdrawal/Infusion", "Withdrawal"),
#         ("continuous", "con", "Continuous", "Infusion")
#         ])
#     def test_that_GIVEN_a_device_running_not_in_infusion_or_withdrawal_mode_WHEN_the_direction_is_reverse_THEN_the_devices_direction_has_not_changed_and_NA_is_triggered(self, _, mode_symbol, mode_name, expected_direction):
#         # Given:
#         self.ca.set_pv_value("MODE:SP", mode_symbol)
#         self.ca.assert_that_pv_is("MODE", mode_name)
#
#         self._start_running()
#         self.ca.assert_that_pv_is("DIRECTION", expected_direction)
#         self.ca.assert_that_pv_is("STATUS", expected_direction)
#
#         # When:
#         self.ca.set_pv_value("DIRECTION:REV", 1)
#
#         # Then:
#         self.ca.assert_that_pv_is("DIRECTION", expected_direction)
#         self.ca.assert_that_pv_is("NA", "Can't run command")
#
#
# class NATests(unittest.TestCase):
#     def setUp(self):
#         # Given
#         self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
#         self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
#         self._reset_device()
#
#     def _reset_device(self):
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         self._lewis.backdoor_run_function_on_device("clear_last_error")
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#
#         self.ca.set_pv_value("MODE:SP", "i")
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#         self.ca.assert_that_pv_is("NA", "")
#
#     def _start_running(self):
#         self.ca.set_pv_value("RUN:SP", 1)
#
#     def _stop_running(self):
#         self.ca.set_pv_value("STOP:SP", 1)
#
#     def test_that_GIVEN_a_device_in_withdrawal_mode_WHEN_starting_the_device_THEN_NA_is_not_triggered(self):
#         # Given:
#         self.ca.set_pv_value("MODE:SP", "w")
#         self.ca.assert_that_pv_is("MODE", "Withdrawal")
#
#         # When:
#         self._start_running()
#
#         # Then:
#         self.ca.assert_that_pv_is("NA", "")
#
#     def test_that_GIVEN_a_device_in_withdrawal_mode_with_NA_triggered_WHEN_starting_the_device_THEN_NA_is_reset(self):
#         # Given:
#         self.ca.set_pv_value("MODE:SP", "w")
#         self.ca.assert_that_pv_is("MODE", "Withdrawal")
#
#         self.ca.set_pv_value("NA", 0)
#         self.ca.assert_that_pv_is("NA", "Can't run command")
#
#         # When:
#         self._start_running()
#         self.ca.assert_that_pv_is("STATUS", "Withdrawal")
#
#         # Then:
#         self.ca.assert_that_pv_is("NA", "")
#
#
#     def test_that_GIVEN_a_device_in_infusion_mode_with_NA_triggered_WHEN_starting_the_device_THEN_NA_is_reset(self):
#         # Given:
#
#         self.ca.set_pv_value("NA", 0)
#         self.ca.assert_that_pv_is("NA", "Can't run command")
#
#         # When:
#         self._start_running()
#         self.ca.assert_that_pv_is("STATUS", "Infusion")
#
#         # Then:
#         self.ca.assert_that_pv_is("NA", "")
#
#
# class DiameterTests(unittest.TestCase):
#     def setUp(self):
#         # Given
#         self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
#         self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
#         self._reset_device()
#
#     def _reset_device(self):
#         self._stop_running()
#         self.ca.assert_that_pv_is("STATUS", "Stopped")
#
#         self._lewis.backdoor_run_function_on_device("clear_last_error")
#         self.ca.process_pv("ERROR")
#         self.ca.assert_that_pv_is("ERROR", "No error")
#
#         self.ca.set_pv_value("MODE:SP", "i")
#         self.ca.assert_that_pv_is("MODE", "Infusion")
#
#         self.ca.assert_that_pv_is("NA", "")
#
#     def _start_running(self):
#         self.ca.set_pv_value("RUN:SP", 1)
#
#     def _stop_running(self):
#         self.ca.set_pv_value("STOP:SP", 1)
#
#     @parameterized.expand([
#         ("10.05", 10.05),
#         ("01.45", 01.45),
#         ("00.0100000000", 00.0100000000),
#         ("99.87", 99.87)
#     ])
#     def test_that_WHEN_the_diameter_is_set_THEN_it_is_set(self, _, value):
#         # Then:
#         self.ca.assert_setting_setpoint_sets_readback(value, "DIAMETER", "DIAMETER:SP")
#

class VolumeTests(unittest.TestCase):
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

        self.ca.assert_that_pv_is("NA", "")

    def _stop_running(self):
        self.ca.set_pv_value("STOP:SP", 1)

    @parameterized.expand([
        (123, 'ml'),
        (123, 'ul'),
        (1, 'ml'),
        (9999, 'ml'),
        (99.87, 'ml'),
        (123.7, 'ml'),
        (1.237, 'ml')
    ])
    def test_GIVEN_value_then_units_set_volume_infusion_WHEN_set_to_various_THEN_read_back_is_value(self, value, units):

        self.ca.set_pv_value("VOL:INF:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "VOL:INF", "VOL:INF:SP")
        self.ca.assert_that_pv_is("VOL:INF:UNITS", units)
        self.ca.assert_that_pv_is("VOL:INF.EGU", units)
        self.ca.assert_that_pv_is("VOL:INF:UNITS:SP", units)
        self.ca.assert_that_pv_is("VOL:INF:SP.EGU", units)

    def test_GIVEN_infusion_unit_set_in_device_WHEN_nothing_THEN_units_are_set_on_readback(self):
        ul = "ul"
        self._lewis.backdoor_set_on_device("infusion_volume_units", ul)
        self.ca.assert_that_pv_is("VOL:INF:UNITS", ul)
        self.ca.assert_that_pv_is("VOL:INF.EGU", ul)

        ml = "ml"
        self._lewis.backdoor_set_on_device("infusion_volume_units", ml)
        self.ca.assert_that_pv_is("VOL:INF:UNITS", ml)
        self.ca.assert_that_pv_is("VOL:INF.EGU", ml)

    @parameterized.expand([
        (123, 'ml'),
        (123, 'ul'),
        (1, 'ml'),
        (9999, 'ml'),
        (99.87, 'ml'),
        (123.7, 'ml'),
        (1.237, 'ml')
    ])
    def test_GIVEN_value_then_units_set_volume_withdraw_WHEN_set_to_various_THEN_read_back_is_value(self, value, units):

        self.ca.set_pv_value("VOL:WDR:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "VOL:WDR", "VOL:WDR:SP")
        self.ca.assert_that_pv_is("VOL:WDR:UNITS", units)
        self.ca.assert_that_pv_is("VOL:WDR.EGU", units)
        self.ca.assert_that_pv_is("VOL:WDR:UNITS:SP", units)
        self.ca.assert_that_pv_is("VOL:WDR:SP.EGU", units)

    def test_GIVEN_withdrawal_unit_set_in_device_WHEN_nothing_THEN_units_are_set_on_readback(self):
        ul = "ul"
        self._lewis.backdoor_set_on_device("withdrawal_volume_units ", ul)
        self.ca.assert_that_pv_is("VOL:WDR:UNITS", ul)
        self.ca.assert_that_pv_is("VOL:WDR.EGU", ul)

        ml = "ml"
        self._lewis.backdoor_set_on_device("withdrawal_volume_units ", ml)
        self.ca.assert_that_pv_is("VOL:WDR:UNITS", ml)
        self.ca.assert_that_pv_is("VOL:WDR.EGU", ml)

    @parameterized.expand([
        (123, 'ml/m'),
        (123, 'ul/m'),
        (1, 'ml/h'),
        (9999, 'ul/h'),
        (99.87, 'ml/h'),
        (123.7, 'ml/h'),
        (1.237, 'ml/h')
    ])
    def test_GIVEN_set_infusion_rate_and_units_WHEN_set_to_various_THEN_read_back_is_value_with_units(self, value, units):

        self.ca.set_pv_value("RATE:INF:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "RATE:INF", "RATE:INF:SP")
        self.ca.assert_that_pv_is("RATE:INF:UNITS", units)
        self.ca.assert_that_pv_is("RATE:INF.EGU", units)
        self.ca.assert_that_pv_is("RATE:INF:UNITS:SP", units)
        self.ca.assert_that_pv_is("RATE:INF:SP.EGU", units)

    @parameterized.expand([
        (123, 'ml/m'),
        (123, 'ul/m'),
        (1, 'ml/h'),
        (9999, 'ul/h'),
        (99.87, 'ml/h'),
        (123.7, 'ml/h'),
        (1.237, 'ml/h')
    ])
    def test_GIVEN_set_withdrawal_rate_and_units_WHEN_set_to_various_THEN_read_back_is_value_with_units(self, value, units):

        self.ca.set_pv_value("RATE:WDR:UNITS:SP", units)

        self.ca.assert_setting_setpoint_sets_readback(value, "RATE:WDR", "RATE:WDR:SP")
        self.ca.assert_that_pv_is("RATE:WDR:UNITS", units)
        self.ca.assert_that_pv_is("RATE:WDR.EGU", units)
        self.ca.assert_that_pv_is("RATE:WDR:UNITS:SP", units)
        self.ca.assert_that_pv_is("RATE:WDR:SP.EGU", units)
