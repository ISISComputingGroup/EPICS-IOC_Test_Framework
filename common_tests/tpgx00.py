import abc
import contextlib
import itertools
from enum import Enum, unique

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim


@unique
class ChannelStatus(Enum):
    DATA_OK = ("Measured data okay", "NO_ALARM")
    UNDERRANGE = ("Underrange", "MINOR")
    OVERRANGE = ("Overrange", "MINOR")
    POINT_ERROR = ("Point error", "MAJOR")
    POINT_OFF = ("Point switched off", "MAJOR")
    NO_HARDWARE = ("No hardware", "INVALID")

    def __new__(cls, value, sevr):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.sevr = sevr
        return obj


CHANNELS = "A1", "A2", "B1", "B2"
TEST_PRESSURES = 1.23, -10.23, 8, 1e-6, 1e6


class ErrorStatus(Enum):
    NO_ERROR = "No error"
    DEVICE_ERROR = "Device error"
    NO_HARDWARE = "No hardware"
    INVALID_PARAM = "Invalid parameter"
    SYNTAX_ERROR = "Syntax error"


class SFStatus(Enum):
    OFF = 0
    ON = 1


class Tpgx00Base:
    """
    Tests for the TPGx00.
    """

    @abc.abstractmethod
    def get_prefix(self):
        pass

    @abc.abstractmethod
    def get_units(self):
        pass

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tpgx00", self.get_prefix())
        self.ca = ChannelAccess(20, device_prefix=self.get_prefix(), default_wait_time=0.0)

        # Reset switching function
        self._set_switching_function("1")
        self._set_switching_function_thresholds(0.0, 0.0, 1)

        # Reset pressure status for each channel to okay
        for channel in CHANNELS:
            self._lewis.backdoor_run_function_on_device(
                "backdoor_set_pressure_status", [channel, ChannelStatus.DATA_OK.name]
            )

    def tearDown(self):
        self._connect_emulator()

    def _set_pressure(self, expected_pressure, channel):
        prop = "pressure_{}".format(channel.lower())
        pv = "SIM:PRESSURE"
        self._lewis.backdoor_set_on_device(prop, expected_pressure)
        self._ioc.set_simulated_value(pv, expected_pressure)

    def _set_switching_function(self, function):
        self.ca.set_pv_value("FUNCTION", function)

    def _set_switching_function_thresholds(self, threshold_low, threshold_high, circuit_assignment):
        self.ca.set_pv_value("FUNCTION:LOW:SP", threshold_low)
        self.ca.set_pv_value("FUNCTION:HIGH:SP", threshold_high)
        self.ca.set_pv_value("FUNCTION:ASSIGN:SP", circuit_assignment)
        self.ca.process_pv("FUNCTION:ASSIGN:SP:OUT")

    def _check_switching_function_thresholds(
        self, function, threshold_low, threshold_high, circuit_assignment
    ):
        self.ca.assert_that_pv_is_number(
            "FUNCTION:" + function + ":LOW:SP:RBV", threshold_low, timeout=15
        )
        self.ca.assert_that_pv_is_number(
            "FUNCTION:" + function + ":HIGH:SP:RBV", threshold_high, timeout=15
        )
        self.ca.assert_that_pv_is(
            "FUNCTION:" + function + ":ASSIGN:SP:RBV", circuit_assignment, timeout=15
        )

    def _check_alarm_status_rbvs(self, alarm):
        for channel in self.get_switching_fns():
            self.ca.assert_that_pv_alarm_is("FUNCTION:" + channel + ":RB", alarm)
            self.ca.assert_that_pv_alarm_is("FUNCTION:" + channel + ":LOW:SP:RBV", alarm)
            self.ca.assert_that_pv_alarm_is("FUNCTION:" + channel + ":HIGH:SP:RBV", alarm)
            self.ca.assert_that_pv_alarm_is("FUNCTION:" + channel + ":ASSIGN:SP:RBV", alarm)

    def _check_alarm_status_function_statuses(self, alarm):
        self.ca.assert_that_pv_alarm_is("FUNCTION:STATUS:RB", alarm)
        for channel in ("1", "2", "3", "4"):
            self.ca.assert_that_pv_alarm_is("FUNCTION:STATUS:" + channel + ":RB", alarm)

    def _connect_emulator(self):
        self._lewis.backdoor_run_function_on_device("connect")

    @contextlib.contextmanager
    def _disconnect_device(self):
        self._lewis.backdoor_run_function_on_device("disconnect")
        try:
            yield
        finally:
            self._connect_emulator()

    def test_that_GIVEN_a_connected_emulator_WHEN_ioc_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skip_if_recsim("Requires emulator")
    def test_that_GIVEN_a_connected_emulator_WHEN_units_are_set_THEN_unit_is_the_same_as_backdoor(
        self,
    ):
        for unit in self.get_units():
            expected_unit = unit.name
            self.ca.set_pv_value("UNITS:SP", expected_unit)
            self._lewis.assert_that_emulator_value_is("backdoor_get_unit", str(expected_unit))
            self.ca.assert_that_pv_is("UNITS:SP", expected_unit)
            self.ca.assert_that_pv_is("UNITS", expected_unit)

    @parameterized.expand(parameterized_list(itertools.product(TEST_PRESSURES, CHANNELS)))
    def test_that_GIVEN_a_connected_emulator_and_pressure_value_WHEN_set_pressure_is_set_THEN_the_ioc_is_updated(
        self, _, expected_pressure, channel
    ):
        pv = "PRESSURE_{}".format(channel)
        self._set_pressure(expected_pressure, channel)
        self.ca.assert_that_pv_is(pv, expected_pressure)

    @parameterized.expand(parameterized_list(CHANNELS))
    @skip_if_recsim("Recsim is unable to simulate a disconnected device")
    def test_that_GIVEN_a_disconnected_emulator_WHEN_getting_pressure_THEN_INVALID_alarm_shows(
        self, _, channel
    ):
        pv = "PRESSURE_{}".format(channel)
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)
        with self._disconnect_device():
            self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.INVALID)

        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(CHANNELS))
    @skip_if_recsim("Requires emulator")
    def test_GIVEN_pressure_status_changed_THEN_pressure_status_and_pressure_severity_updated(
        self, _, channel
    ):
        for status in ChannelStatus:
            self._lewis.backdoor_run_function_on_device(
                "backdoor_set_pressure_status", [channel, status.name]
            )
            self._set_pressure(TEST_PRESSURES[0], channel)
            self.ca.assert_that_pv_is(f"PRESSURE_{channel}_STAT", status.value, timeout=15)
            self.ca.assert_that_pv_is(f"PRESSURE_{channel}_STAT.SEVR", status.sevr, timeout=15)
            self.ca.assert_that_pv_is(f"PRESSURE_{channel}.SEVR", status.sevr, timeout=15)

    # Only test using switching function values in [1-4]; these are values that are valid between both models. Invalid values are checked in the
    # individual submodules.
    @parameterized.expand(
        [
            ("1", 0.5e2, 1.7e-5, 0.5e2, 1.7e-5),
            ("2", 9.95e-3, 1e4, 1.0e-2, 9.9e3),
            ("4", 12e-215, 1e215, 1e-11, 9.9e3),
        ]
    )
    @skip_if_recsim("Requires emulator")
    def test_GIVEN_function_thresholds_set_THEN_thresholds_readback_correct(
        self,
        switching_func,
        set_threshold_low,
        set_threshold_hi,
        read_threshold_low,
        read_threshold_hi,
    ):
        for circuit_assign in self.get_sf_assignment():
            self._set_switching_function(switching_func)
            self._set_switching_function_thresholds(
                set_threshold_low, set_threshold_hi, circuit_assign.value
            )
            self._check_switching_function_thresholds(
                str(switching_func), read_threshold_low, read_threshold_hi, circuit_assign.desc
            )

    @skip_if_recsim("Requires emulator")
    def test_GIVEN_thresholds_settings_and_pressure_above_THEN_check_if_violation_detected(self):
        self._set_pressure(0, "A2")
        self._set_switching_function("3")
        # Use enum value 4 for circuit assignment as this is an edge case; it should yield different states for the two models.
        switching_fn_4 = self.get_sf_assignment()(4)
        self._set_switching_function_thresholds(5e2, 7.5e4, switching_fn_4.value)
        self.ca.assert_that_pv_is("FUNCTION:3:THRESHOLD:BELOW", 1)
        self._set_pressure(6.43, switching_fn_4.desc)
        self.ca.assert_that_pv_is("FUNCTION:3:THRESHOLD:BELOW", 1)
        self._set_pressure(501.0, switching_fn_4.desc)
        self.ca.assert_that_pv_is("FUNCTION:3:THRESHOLD:BELOW", 0)

    @skip_if_recsim("Requires emulator")
    def test_WHEN_device_disconnected_THEN_rbv_values_go_into_alarm(self):
        self._check_alarm_status_rbvs(self.ca.Alarms.NONE)
        with self._disconnect_device():
            self._check_alarm_status_rbvs(self.ca.Alarms.INVALID)

        self._check_alarm_status_rbvs(self.ca.Alarms.NONE)

    def _check_switching_function_statuses(self, expected_statuses):
        self.ca.assert_that_pv_is("FUNCTION:STATUS:1:RB", str(SFStatus[expected_statuses[0]].value))
        self.ca.assert_that_pv_is("FUNCTION:STATUS:2:RB", str(SFStatus[expected_statuses[1]].value))
        self.ca.assert_that_pv_is("FUNCTION:STATUS:3:RB", str(SFStatus[expected_statuses[2]].value))
        self.ca.assert_that_pv_is("FUNCTION:STATUS:4:RB", str(SFStatus[expected_statuses[3]].value))

    @skip_if_recsim("Requires emulator")
    def test_GIVEN_function_status_set_THEN_readback_correct(self):
        function_statuses = ["OFF", "OFF", "ON", "ON", "OFF", "ON"]
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_switching_function_status", [function_statuses]
        )
        self._check_switching_function_statuses(function_statuses)

    @skip_if_recsim("Requires emulator")
    def test_WHEN_error_set_by_device_THEN_readback_correct(self):
        for error in ErrorStatus:
            self._lewis.backdoor_run_function_on_device("backdoor_set_error_status", [error.name])
            self.ca.assert_that_pv_is("ERROR", error.value)

    @skip_if_recsim("Requires emulator")
    def test_WHEN_device_disconnected_THEN_function_statuses_go_into_alarm(self):
        self._check_alarm_status_function_statuses(self.ca.Alarms.NONE)
        with self._disconnect_device():
            self._check_alarm_status_function_statuses(self.ca.Alarms.INVALID)

        self._check_alarm_status_function_statuses(self.ca.Alarms.NONE)

    @parameterized.expand(
        [
            ("1"),
            ("2"),
        ]
    )
    @skip_if_recsim("Requires emulator")
    def test_WHEN_underrange_macro_is_set_THEN_alarm_is_none(self, channel):
        with self._ioc.start_with_macros(
            {
                "TPG_UNDERRANGE_ALARM_SEVERITY_CHAN" + channel: "NO_ALARM",
            },
            pv_to_wait_for="PRESSURE_A" + channel + "_STAT",
        ):
            self._lewis.backdoor_run_function_on_device(
                "backdoor_set_pressure_status", ["A" + channel, ChannelStatus.UNDERRANGE.name]
            )
            self._lewis.backdoor_run_function_on_device(
                "backdoor_set_pressure_status", ["B" + channel, ChannelStatus.UNDERRANGE.name]
            )

            self.ca.assert_that_pv_alarm_is("PRESSURE_A" + channel + "_STAT", self.ca.Alarms.NONE)
            self.ca.assert_that_pv_alarm_is("PRESSURE_B" + channel + "_STAT", self.ca.Alarms.NONE)

    @parameterized.expand(
        [
            ("1"),
            ("2"),
        ]
    )
    @skip_if_recsim("Requires emulator")
    def test_WHEN_underrange_macro_is_not_set_THEN_alarm_is_minor(self, channel):
        with self._ioc.start_with_macros({}, pv_to_wait_for="PRESSURE_A" + channel + "_STAT"):
            self._lewis.backdoor_run_function_on_device(
                "backdoor_set_pressure_status", ["A" + channel, ChannelStatus.UNDERRANGE.name]
            )
            self._lewis.backdoor_run_function_on_device(
                "backdoor_set_pressure_status", ["B" + channel, ChannelStatus.UNDERRANGE.name]
            )

            self.ca.assert_that_pv_alarm_is("PRESSURE_A" + channel + "_STAT", self.ca.Alarms.MINOR)
            self.ca.assert_that_pv_alarm_is("PRESSURE_B" + channel + "_STAT", self.ca.Alarms.MINOR)
