"""
Testing using channel access.
"""

import ctypes
import datetime
import operator
import os
import time
from abc import abstractmethod
from contextlib import contextmanager
from functools import partial, partialmethod
from typing import Callable, Generator, Optional

from genie_python.genie import PVValue
from genie_python.genie_cachannel_wrapper import (
    CaChannelWrapper,
    UnableToConnectToPVException,
)
from genie_python.genie_p4p_wrapper import P4PWrapper

from utils.formatters import format_value


class _ValueSource:
    @property
    @abstractmethod
    def value(self) -> PVValue:
        pass


class _MonitorAssertion(_ValueSource):
    """
    This is used to assert the value based on a pv monitor event. It will sign up to the monitor
    call backs and set an internal value when that changes. It will need to poll ca channel for
    events before this can be triggered and it does this when the value is requested.
    """

    def __init__(
        self, channel_access: "ChannelAccess", pv: str, pv_access: Optional[bool] = None
    ) -> None:
        """
        Initialise.
        Args:
            channel_access: channel_access to set up monitor
            pv: name of pv to monitor
        """
        self.pv = pv
        self._full_pv_name = channel_access.create_pv_with_prefix(pv)
        self.all_values = []
        self.latest_value = None
        import global_settings

        self.pv_access = pv_access if pv_access is not None else global_settings.DEFAULT_USE_PVA
        if self.pv_access:
            P4PWrapper.add_monitor(channel_access.create_pv_with_prefix(pv), self._set_val)
        else:
            CaChannelWrapper.add_monitor(channel_access.create_pv_with_prefix(pv), self._set_val)

    def _set_val(self, value: PVValue, alarm_severity: str, alarm_status: str) -> None:
        self.latest_value = value
        self.all_values.append(value)

    @property
    def value(self) -> PVValue:
        """
        Returns: value monitor set
        """
        if not self.pv_access:
            CaChannelWrapper.poll()
        return self.latest_value


class ChannelAccess(object):
    """
    Provides the required channel access commands.
    """

    class Alarms(object):
        """
        Possible alarm states that a PV can be in.
        """

        NONE = "NO_ALARM"  # Alarm value if there is no alarm
        MAJOR = "MAJOR"  # Alarm value if the record is in major alarm
        MINOR = "MINOR"  # Alarm value if the record is in minor alarm
        INVALID = "INVALID"  # Alarm value if the record has a calc alarm
        DISABLE = "DISABLE"  # Alarm stat value if the record has been disabled

    def __init__(
        self,
        default_timeout: float = 5,
        device_prefix: Optional[str] = None,
        default_wait_time: float = 1.0,
        pv_access: Optional[bool] = None,
    ) -> None:
        """
        Initializes this ChannelAccess object.

        Args:
            device_prefix: The device prefix which will be added to the start of all pvs.
            default_timeout: The default time out to wait for an assertion on a PV to become true.
            default_wait_time: The default time to wait after a set_pv_value
        Returns:
            None.
        """
        import global_settings

        self.pv_access = pv_access if pv_access is not None else global_settings.DEFAULT_USE_PVA
        if self.pv_access:
            self.ca = P4PWrapper()
        else:
            self.ca = CaChannelWrapper()
        self.default_wait_time = default_wait_time

        # Silence CA errors
        if self.pv_access:
            P4PWrapper.error_log_function = lambda *a, **kw: None
        else:
            CaChannelWrapper.error_log_func = lambda *a, **kw: None
        try:
            hcom = ctypes.cdll.LoadLibrary("COM.DLL")
            hcom.eltc(ctypes.c_int(0))
        except Exception as e:
            print("Unable to disable CA errors: ", e)

        self.host_prefix = os.environ["testing_prefix"]
        self._default_timeout = default_timeout
        if not self.host_prefix.endswith(":"):
            self.host_prefix += ":"

        self.prefix = self.host_prefix
        if device_prefix is not None:
            self.prefix += f"{device_prefix}:"

    def set_pv_value(
        self,
        pv: str,
        value: PVValue,
        prefix: Optional[str] = None,
        wait: bool = False,
        sleep_after_set: Optional[float] = None,
    ) -> None:
        """
        Sets the specified PV to the supplied value.

        Args:
            pv: the EPICS PV name
            value: the value to set
            prefix: the preix to use (default: "<instrument>:<ioc>:")
            wait: wait for completion callback (default: False)
            sleep_after_set: before a sleep after setting pv value
        """
        if prefix is None:
            prefix = self.prefix

        # Take note of original prefix in case it is temporarily modified by paramter
        original_prefix = self.prefix
        self.prefix = prefix

        if sleep_after_set is None:
            sleep_after_set = self.default_wait_time
        # Wait for the PV to exist before writing to it. If this is not here sometimes the tests try
        # to jump the gun and attempt to write to a PV that doesn't exist yet
        self.assert_that_pv_exists(pv)

        # Don't use wait=True because it will cause an infinite wait if the value never gets set
        # successfully In that case the test should fail (because the correct value is not set)
        # but it should not hold up all the other tests
        self.ca.set_pv_value(
            self.create_pv_with_prefix(pv), value, wait=wait, timeout=self._default_timeout
        )

        # Reset original prefix in case it was temporarily changed
        self.prefix = original_prefix

        # Give lewis time to process - avoid sleep(0) in case it might do am implicit thread yield
        if sleep_after_set > 0.0:
            time.sleep(sleep_after_set)

    def get_pv_value(self, pv: str) -> PVValue:
        """
        Gets the current value for the specified PV.

        Args:
            pv: the EPICS PV name
        Returns:
            the current value
        """
        return self.ca.get_pv_value(self.create_pv_with_prefix(pv))

    def process_pv(self, pv: str) -> None:
        """
        Makes the pv process once.

        Args:
            pv: the EPICS PV name
        """
        pv_proc = "{}.PROC".format(self.create_pv_with_prefix(pv))
        return self.ca.set_pv_value(pv_proc, 1)

    @contextmanager
    def put_simulated_record_into_alarm(self, pv: str, alarm: str) -> Generator[None, None, None]:
        """
        Put a simulated record into alarm. Using a context manager to put PVs into alarm means they
        don't accidentally get left in alarm if the test fails.

        Args:
             pv: pv to put into alarm
             alarm: type of alarm
        Raises:
            AssertionError if the simulated alarm status could not be set.
        """

        def _set_and_check_simulated_alarm(set_check_pv: str, set_check_alarm: str) -> None:
            self.set_pv_value("{}.SIMS".format(set_check_pv), set_check_alarm)
            self.assert_that_pv_alarm_is("{}".format(set_check_pv), set_check_alarm)

        try:
            _set_and_check_simulated_alarm(pv, alarm)
            yield
        finally:
            _set_and_check_simulated_alarm(pv, self.Alarms.NONE)

    def create_pv_with_prefix(self, pv: str) -> str:
        """
        Create the full pv name with instrument prefix.

        Args:
            pv: pv name without prefix
        Returns:
            pv name with prefix
        """
        return "{prefix}{pv}".format(prefix=self.prefix, pv=pv)

    def _wait_for_pv_lambda(
        self, wait_for_lambda: Callable[[], PVValue], timeout: Optional[float] = None
    ) -> PVValue:
        """
        Wait for a lambda containing a pv to become None; return value or timeout and return actual
        value.

        Args:
            wait_for_lambda: lambda we expect to be None
            timeout: time out period
        Returns:
            final value of lambda
        """
        start_time = time.time()
        current_time = start_time

        if timeout is None:
            timeout = self._default_timeout

        while current_time - start_time < timeout:
            try:
                lambda_value = wait_for_lambda()
                if lambda_value is None:
                    return lambda_value
            except UnableToConnectToPVException:
                pass  # try again next loop maybe the PV will be up

            time.sleep(0.01)
            current_time = time.time()

        # last try
        return wait_for_lambda()

    def assert_that_pv_value_causes_func_to_return_true(
        self,
        pv: str,
        func: Callable[[PVValue], bool],
        timeout: Optional[float] = None,
        message: Optional[str] = None,
        pv_value_source: Optional[_ValueSource] = None,
    ) -> None:
        """
        Check that a PV satisfies a given function within some timeout.

        Args:
            pv: the PV to check
            func: a function that takes one argument, the PV value, and returns True if the value is
             valid.
            timeout: time to wait for the PV to satisfy the function
            message: custom message to print on failure
            pv_value_source: place to get value from; None from pv get; otherwise attribute value
            will be used
        Raises:
            AssertionError: If the function does not evaluate to true within the given timeout
        """

        def _wrapper(message: str) -> str | None:
            if pv_value_source is None:
                value = self.get_pv_value(pv)
            else:
                value = pv_value_source.value
            try:
                return_value = func(value)
            except Exception as e:
                return (
                    f"Exception was thrown while evaluating function '{func.__name__}' on pv"
                    f" value {format_value(value)}. Exception was: {e.__class__.__name__} {e}"
                )
            if return_value:
                return None
            else:
                return "Exception date time: {}{}{}{}{}".format(
                    datetime.datetime.now(),
                    os.linesep,
                    message,
                    os.linesep,
                    "Final PV value was {}".format(format_value(value)),
                )

        if message is None:
            message = "Expected function '{}' to evaluate to True when reading PV '{}'.".format(
                func.__name__, self.create_pv_with_prefix(pv)
            )

        err = self._wait_for_pv_lambda(partial(_wrapper, message), timeout)
        if err is not None:
            raise AssertionError(err)

    def assert_that_pv_is(
        self,
        pv: str,
        expected_value: PVValue,
        timeout: Optional[float] = None,
        msg: Optional[str] = None,
        pv_value_source: Optional[_ValueSource] | None = None,
    ) -> None:
        """
        Assert that the pv has the expected value or that it becomes the expected value within the
        timeout.

        Args:
            pv: pv name
            expected_value: expected value
            timeout: if it hasn't changed within this time raise assertion error
            msg: Extra message to print
            pv_value_source: place to get pv value from on get; None pv is read using caget;
            otherwise attribute value will be used
        Raises:
            AssertionError: if value does not become requested value
            UnableToConnectToPVException: if pv does not exist within timeout
        """

        if msg is None:
            msg = "Expected PV, '{}' to have value {}.".format(
                self.create_pv_with_prefix(pv), format_value(expected_value)
            )

        return self.assert_that_pv_value_causes_func_to_return_true(
            pv,
            lambda val: val == expected_value,
            timeout=timeout,
            message=msg,
            pv_value_source=pv_value_source,
        )

    @staticmethod
    def _normalise_path(path: PVValue) -> str:
        """
        Normalise a path and it's case (useful for comparisons)

        Args:
            path (str): The path to normalise
        Returns:
            str: The normalised path
        """
        assert isinstance(path, str)
        return os.path.normpath(os.path.normcase(path))

    def assert_that_pv_is_path(
        self,
        pv: str,
        expected_path: str,
        timeout: Optional[float] = None,
        msg: Optional[str] = None,
        pv_value_source: Optional[_ValueSource] = None,
    ) -> None:
        """
        Assert that a pv is a path that when normalised matches the expected path.

        Args:
            pv: pv name
            expected_path: expected path
            timeout: if it hasn't changed within this time raise assertion error
            msg: Extra message to print
            pv_value_source: place to get pv value from on get; None pv is read using caget;
              otherwise attribute value will be used
        Raises:
            AssertionError: if value does not become requested value
            UnableToConnectToPVException: if pv does not exist within timeout
        """
        normalised_expected_path = self._normalise_path(expected_path)
        if msg is None:
            msg = "Expected PV, '{}' to have path {}.".format(
                self.create_pv_with_prefix(pv), format_value(normalised_expected_path)
            )

        return self.assert_that_pv_value_causes_func_to_return_true(
            pv,
            lambda val: self._normalise_path(val) == normalised_expected_path,
            timeout=timeout,
            message=msg,
            pv_value_source=pv_value_source,
        )

    def assert_that_pv_after_processing_is(
        self,
        pv: str,
        expected_value: PVValue,
        timeout: Optional[float] = None,
        msg: Optional[str] = None,
    ) -> None:
        """
        Assert that the pv has the expected value after the pv is processed
        or that it becomes the expected value within the timeout.

        Args:
            pv: pv name
            expected_value: expected value
            timeout: if it hasn't changed within this time raise assertion error
            msg: Extra message to print
        Raises:
            AssertionError: if value does not become requested value
            UnableToConnectToPVException: if pv does not exist within timeout
        """

        self.process_pv(pv)
        return self.assert_that_pv_is(pv, expected_value, timeout=None, msg=None)

    def assert_that_pv_is_not(
        self,
        pv: str,
        restricted_value: PVValue,
        timeout: Optional[float] = None,
        msg: Optional[str] = None,
    ) -> None:
        """
        Assert that the pv does not have a particular value and optionally it does not become that
         value within the timeout.

        Args:
            pv: pv name
            restricted_value: value the PV shouldn't become
            timeout: if it becomes the value within this time, raise an assertion error
            msg: Extra message to print
        Raises:
            AssertionError: if value has the restricted value
            UnableToConnectToPVException: if pv does not exist within timeout
        """
        if msg is None:
            msg = "Expected PV to not have value {}.".format(format_value(restricted_value))

        return self.assert_that_pv_value_causes_func_to_return_true(
            pv, lambda val: val != restricted_value, timeout, message=msg
        )

    @staticmethod
    def _within_tolerance_condition(val: PVValue, expected: float, tolerance: float) -> bool:
        """
        Condition to tell whether a number is equal to another within a tolerance.

        Args:
            val: The actual value
            expected: The expected value
            tolerance:
        Returns:
            True if within tolerance, False otherwise.
        """
        try:
            assert isinstance(val, (float, int, str))
            val = float(val)
        except (ValueError, TypeError):
            return False
        return abs(val - expected) <= tolerance

    def assert_that_pv_is_number(
        self,
        pv: str,
        expected: float,
        tolerance: float = 0.0,
        timeout: Optional[float] = None,
        pv_value_source: Optional[_ValueSource] = None,
    ) -> None:
        """
        Assert that the pv has the expected value or that it becomes the expected value within the
        timeout

        Args:
            pv: pv name
            expected: expected value
            tolerance: the allowable deviation from the expected value
            timeout: if it hasn't changed within this time raise assertion error
            pv_value_source: where to get the value from, None for caget from pv
        Raises:
            AssertionError: if value does not become requested value
            UnableToConnectToPVException: if pv does not exist within timeout
        """
        message = "Expected PV '{}' value to be equal to {} (tolerance: {})".format(
            self.create_pv_with_prefix(pv), format_value(expected), format_value(tolerance)
        )

        return self.assert_that_pv_value_causes_func_to_return_true(
            pv,
            lambda val: self._within_tolerance_condition(val, expected, tolerance),
            timeout,
            message=message,
            pv_value_source=pv_value_source,
        )

    def assert_that_pv_is_not_number(
        self, pv: str, restricted: float, tolerance: float = 0, timeout: Optional[float] = None
    ) -> None:
        """
        Assert that the pv is at least tolerance from the restricted value within the timeout

        Args:
             pv: pv name
             restricted: the value we don't want the PV to have
             tolerance: the minimal deviation from the expected value
             timeout: if it hasn't changed within this time raise assertion error
        Raises:
             AssertionError: if value does not enter the desired range
             UnableToConnectToPVException: if pv does not exist within timeout
        """
        message = "Expected PV value to be not equal to {} (tolerance: {})".format(
            format_value(restricted), format_value(tolerance)
        )

        return self.assert_that_pv_value_causes_func_to_return_true(
            pv,
            lambda val: not self._within_tolerance_condition(val, restricted, tolerance),
            timeout,
            message=message,
        )

    def assert_that_pv_after_processing_is_number(
        self,
        pv: str,
        expected_value: float,
        tolerance: float = 0.0,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Assert that the pv has the expected number value after the pv is processed
        or that it becomes the expected number value within the timeout.

        Args:
            pv: The name of the pv to test.
            expected_value: The expected value of the pv.
            tolerance: The allowable deviation from the expected value.
            timeout: If it hasn't changed within this time raise assertion error.

        Raises:
            AssertionError: If value does not become requested value.
            UnableToConnectToPVException: If pv does not exist within timeout.
        """

        self.process_pv(pv)
        return self.assert_that_pv_is_number(pv, expected_value, tolerance=tolerance, timeout=None)

    def assert_that_pv_is_one_of(
        self, pv: str, expected_values: list[PVValue], timeout: Optional[float] = None
    ) -> None:
        """
        Assert that the pv has one of the expected values or that it becomes one of the expected
        value within the timeout.

        Args:
             pv: pv name
             expected_values: expected values
             timeout: if it hasn't changed within this time raise assertion error
        Raises:
             AssertionError: if value does not become requested value
             UnableToConnectToPVException: if pv does not exist within timeout
        """

        def _condition(val: PVValue) -> bool:
            return val in expected_values

        message = "Expected PV value to be in {}".format(expected_values)
        return self.assert_that_pv_value_causes_func_to_return_true(
            pv, _condition, timeout, message
        )

    def assert_that_pv_is_within_range(
        self,
        pv: str,
        min_value: int | float,
        max_value: int | float,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Assert that the pv is within or at the bounds of the ranges  between a minimum and maximum
        within the timeout

        Args:
             pv: pv name
             min_value: minimum value (inclusive)
             max_value: maximum value (inclusive)
             timeout: if it hasn't changed within this time raise assertion error
        Raises:
             AssertionError: if value does not become requested value
             UnableToConnectToPVException: if pv does not exist within timeout
        """

        def _condition(val: PVValue) -> bool:
            assert isinstance(val, (int, float, str))
            return min_value <= float(val) <= max_value

        message = "Expected PV value to between {} and {}".format(min_value, max_value)
        return self.assert_that_pv_value_causes_func_to_return_true(
            pv, _condition, timeout, message
        )

    def assert_that_pv_exists(self, pv: str, timeout: Optional[float] = None) -> None:
        """
        Wait for pv to be available or timeout and throw UnableToConnectToPVException.

        Args:
             pv: pv to wait for
             timeout: time to wait for
        Raises:
             AssertionError: if pv can not be connected to after given time
        """
        if timeout is None:
            timeout = self._default_timeout

        start_time = time.time()
        pv = self.create_pv_with_prefix(pv)
        while time.time() - start_time < timeout:
            if self.ca.pv_exists(pv, timeout=1.0):
                break
        else:
            # Last try.
            if not self.ca.pv_exists(pv, timeout=1.0):
                raise AssertionError(
                    "Exception date time: {time}\nPV {pv} does not exist".format(
                        time=datetime.datetime.now(), pv=pv
                    )
                )

    def assert_that_pv_does_not_exist(self, pv: str, timeout: float = 2) -> None:
        """
        Asserts that a pv does not exist.

        Args:
             pv: pv to wait for
             timeout: amount of time to wait for
        Raises:
             AssertionError: if pv exists
        """
        try:
            self.assert_that_pv_exists(pv, timeout)
        except AssertionError:
            return
        else:
            raise AssertionError("PV {pv} exists".format(pv=self.create_pv_with_prefix(pv)))

    def assert_that_pv_alarm_is_not(
        self, pv: str, alarm: str, timeout: Optional[float] = None
    ) -> None:
        """
        Assert that a pv is not in alarm state given or timeout.

        Args:
             pv: pv name
             alarm: alarm state (see constants ALARM_X)
             timeout: length of time to wait for change
        Raises:
             AssertionError: if alarm is requested value
             UnableToConnectToPVException: if pv does not exist within timeout
        """
        return self.assert_that_pv_is_not("{}.SEVR".format(pv), alarm, timeout=timeout)

    def assert_that_pv_alarm_is(self, pv: str, alarm: str, timeout: Optional[float] = None) -> None:
        """
        Assert that a pv is in alarm state given or timeout.
        Checks the SERV of the pv name with any field name removed.

        Args:
             pv: pv name
             alarm: alarm state (see constants ALARM_X)
             timeout: length of time to wait for change
        Raises:
             AssertionError: if alarm does not become requested value
             UnableToConnectToPVException: if pv does not exist within timeout
        """
        pv_no_field = pv.rsplit(".", 1)[0]
        return self.assert_that_pv_is("{}.SEVR".format(pv_no_field), alarm, timeout=timeout)

    def assert_setting_setpoint_sets_readback(
        self,
        value: PVValue,
        readback_pv: str,
        set_point_pv: Optional[str] = None,
        expected_value: PVValue = None,
        expected_alarm: Optional[str] = Alarms.NONE,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Set a pv to a value and check that the readback has the expected value and alarm state.

        Args:
             value: value to set
             readback_pv: the pv for the read back (e.g. IN:INST:TEMP)
             set_point_pv: the pv to check has the correct value;
            if None use the readback with SP  (e.g. IN:INST:TEMP:SP)
             expected_value: the expected return value; if None use the value
             expected_alarm: the expected alarm status, None don't check; defaults to ALARM_NONE
             timeout: timeout for the pv and alarm to become the expected values
        Raises:
             AssertionError: if setback does not become expected value or has incorrect alarm state
             UnableToConnectToPVException: if a pv does not exist within timeout
        """
        if set_point_pv is None:
            set_point_pv = "{}:SP".format(readback_pv)
        if expected_value is None:
            expected_value = value

        self.set_pv_value(set_point_pv, value, sleep_after_set=0)
        self.assert_that_pv_is(readback_pv, expected_value, timeout=timeout)
        if expected_alarm is not None:
            self.assert_that_pv_alarm_is(readback_pv, expected_alarm, timeout=timeout)

    def assert_that_pv_value_over_time_satisfies_comparator(
        self, pv: str, wait: float, comparator: Callable[[PVValue, PVValue], bool]
    ) -> None:
        """
        Check that a PV satisfies a given function over time. The initial value is compared to the
         final value after a given time using the comparator.

        Args:
             pv: the PV to check
             wait: the number of seconds to wait
             comparator: a function taking two arguments; the initial and final values, which should
              return a boolean
        Raises:
             AssertionError: if the value of the pv did not satisfy the comparator
        """
        initial_value = self.get_pv_value(pv)
        time.sleep(wait)

        message = "Expected value trend to satisfy comparator '{}'. Initial value was {}.".format(
            comparator.__name__, format_value(initial_value)
        )

        def _condition(val: PVValue) -> bool:
            return comparator(val, initial_value)

        return self.assert_that_pv_value_causes_func_to_return_true(pv, _condition, message=message)

    # Special cases of assert_that_pv_value_over_time_satisfies_comparator
    assert_that_pv_value_is_increasing = partialmethod(
        assert_that_pv_value_over_time_satisfies_comparator, comparator=operator.gt
    )

    assert_that_pv_value_is_decreasing = partialmethod(
        assert_that_pv_value_over_time_satisfies_comparator, comparator=operator.lt
    )

    assert_that_pv_value_is_unchanged = partialmethod(
        assert_that_pv_value_over_time_satisfies_comparator, comparator=operator.eq
    )

    assert_that_pv_value_is_changing = partialmethod(
        assert_that_pv_value_over_time_satisfies_comparator, comparator=operator.ne
    )

    @contextmanager
    def assert_that_pv_monitor_gets_values(
        self, pv: str, expected_values: list[PVValue]
    ) -> Generator[None, None, None]:
        """
        Assert that a pv has received a number of values set by a monitor event
        Args:
            pv: the pv name. Must not be the same PV which is written to in the test.
            expected_values (list): list of the expected values
        Raises:
            AssertionError: if the lengths of the lists of expected and monitor values are not equal
            AssertionError: if the value of the pv did not satisfy the comparator
        """
        monitor = _MonitorAssertion(self, pv)

        yield

        if len(expected_values) == len(monitor.all_values):
            for i, expected_value in enumerate(expected_values):
                if expected_value != monitor.all_values[i]:
                    raise AssertionError(
                        f"Monitor got {monitor.all_values[i]}, but expected {expected_value}"
                    )
        else:
            raise AssertionError(
                f"List of Monitor values: {monitor.all_values}, but list of Expected values:"
                f" {expected_values}"
            )

    @contextmanager
    def assert_that_pv_monitor_is(
        self, pv: str, expected_value: PVValue
    ) -> Generator[None, None, None]:
        """
        Assert that a pv has a given value set by a monitor event
        Args:
            pv: the pv name. Must not be the same PV which is written to in the test.
            expected_value: the expected value
        Raises:
            AssertionError: if the value of the pv did not satisfy the comparator
        """
        pv_value_source = _MonitorAssertion(self, pv)

        yield

        self.assert_that_pv_is(pv_value_source.pv, expected_value, pv_value_source=pv_value_source)

    @contextmanager
    def assert_that_pv_monitor_is_number(
        self, pv: str, expected_value: float, tolerance: float = 0.0
    ) -> Generator[None, None, None]:
        """
        Assert that a pv value is set by a monitor event and is within a tolerance
        Args:
            pv: the pv name. Must not be the same PV which is written to in the test.
            expected_value: the expected value
            tolerance: tolerance

        Raises:
             AssertionError: if the value of the pv did not satisfy the comparator
        """
        pv_value_source = _MonitorAssertion(self, pv)

        yield

        self.assert_that_pv_is_number(
            pv, expected_value, tolerance=tolerance, pv_value_source=pv_value_source
        )

    @contextmanager
    def assert_pv_processed(self, pv: str) -> Generator[None, None, None]:
        """
        Asserts that a PV was processed by putting a monitor on the PV and asserting it's called.

        Args:
            pv: the PV on which to check processing
        """
        pv_with_prefix = self.create_pv_with_prefix(pv)

        class PvUpdateTimeValueSource(_ValueSource):
            def __init__(self, pv_access: bool = False) -> None:
                self.pv_access = pv_access

            @property
            def value(self) -> str:
                if self.pv_access:
                    return str(P4PWrapper.get_pv_timestamp(pv_with_prefix))
                return str(CaChannelWrapper.get_pv_timestamp(pv_with_prefix))

        time_before = PvUpdateTimeValueSource(self.pv_access).value

        yield

        self.assert_that_pv_value_causes_func_to_return_true(
            pv=pv_with_prefix,
            func=lambda val: val != time_before,
            pv_value_source=PvUpdateTimeValueSource(),
            message="PV {} was not processed".format(pv),
        )

    @contextmanager
    def assert_pv_not_processed(self, pv: str) -> Generator[None, None, None]:
        """
        Asserts that a PV was processed by getting the time

        Args:
            pv: the PV on which to check (lack of) processing
        """
        pv_with_prefix = self.create_pv_with_prefix(pv)

        class PvUpdateTimeValueSource(_ValueSource):
            def __init__(self, pv_access: bool = False) -> None:
                self.pv_access = pv_access

            @property
            def value(self) -> str:
                if self.pv_access:
                    return str(P4PWrapper.get_pv_timestamp(pv_with_prefix))
                return str(CaChannelWrapper.get_pv_timestamp(pv_with_prefix))

        time_before = PvUpdateTimeValueSource(self.pv_access).value

        yield

        self.assert_that_pv_value_causes_func_to_return_true(
            pv=pv_with_prefix,
            func=lambda val: val == time_before,
            pv_value_source=PvUpdateTimeValueSource(),
            message="PV {} was processed".format(pv),
        )

    def assert_dict_of_pvs_have_given_values(self, pvs_and_values_dict: dict[str, PVValue]) -> None:
        """
        Assert that the pvs (keys of the passed dict) have the given values (values of the dict).

        Args:
            pvs_and_values_dict: A dictionary with keys as pvs and expected values as the value.
        """
        error_message = ""
        for pv, value in pvs_and_values_dict.items():
            try:
                self.assert_that_pv_is(pv, value)
            except AssertionError as e:
                error_message += f"\n{e}"
        if error_message != "":
            raise AssertionError(f"Not all PVs have given values, see errors: {error_message}")
