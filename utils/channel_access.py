import os
import time
from genie_python.genie_cachannel_wrapper import CaChannelWrapper, UnableToConnectToPVException


class ChannelAccess(object):
    """
    Provides the required channel access commands.
    """

    ALARM_NONE = "NO_ALARM"
    """Alarm value if their is no alarm"""

    ALARM_MAJOR = "MAJOR"
    """Alarm value if the record is in major alarm"""

    ALARM_MINOR = "MINOR"
    """Alarm value if the record is in minor alarm"""

    ALARM_INVALID = "INVALID"
    """Alarm value if the record has a calc alarm"""

    def __init__(self):
        """
        Constructor.
        """
        self.ca = CaChannelWrapper()
        self.prefix = os.environ["testing_prefix"]
        if not self.prefix.endswith(':'):
            self.prefix += ':'

    def set_pv_value(self, pv, value):
        """
        Sets the specified PV to the supplied value.

        :param pv: the EPICS PV name
        :param value: the value to set
        """
        self.ca.set_pv_value(self._create_pv_with_prefix(pv), value, wait=True, timeout=5)
        # Need to give Lewis time to process
        time.sleep(1)

    def get_pv_value(self, pv):
        """
        Gets the current value for the specified PV.

        :param pv: the EPICS PV name
        :return: the current value
        """
        return self.ca.get_pv_value(self._create_pv_with_prefix(pv))

    def assert_that_pv_is(self, pv, expected_value, timeout=5):
        """
        Assert that the pv has the expected value or that it becomes the expected value within the timeout.

        :param pv: pv name
        :param expected_value: expected value
        :param timeout: if it hasn't changed within this time raise assertion error
        :raises AssertionError: if value does not become requested value
        :raises UnableToConnectToPVException: if pv does not exist within timeout
        """

        error_message = self._wait_for_pv_lambda(lambda: self._values_match(pv, expected_value), timeout)

        if error_message is None:
            return

        raise AssertionError(error_message)

    def assert_that_pv_is_one_of(self, pv, expected_values, timeout=5):
        """
        Assert that the pv has one of the expected values or that it becomes one of the expected value within the
        timeout.

        :param pv: pv name
        :param expected_values: expected values
        :param timeout: if it hasn't changed within this time raise assertion error
        :return:
        :raises AssertionError: if value does not become requested value
        :raises UnableToConnectToPVException: if pv does not exist within timeout
        """

        error_message = self._wait_for_pv_lambda(lambda: self._value_match_one_of(pv, expected_values), timeout)

        if error_message is None:
            return

        raise AssertionError(error_message)

    def _values_match(self, pv, expected_value):
        """
        Check pv matches a value.

        :param pv: name of the pv (no prefix)
        :param expected_value: value that is expected
        :return: None if they match; error string stating the difference if they do not
        """
        pv_value = self.get_pv_value(pv)
        if pv_value == expected_value:
            return None
        else:
            return "Expected {expected}: actual {actual}".format(expected=expected_value, actual=pv_value)

    def _value_match_one_of(self, pv, expected_values):
        """
        Check pv matches one of a number of values.

        :param pv: name of the pv (no prefix)
        :param expected_values: list of value of of which is expected
        :return: None if they match; error string stating the difference if they do not

        """
        pv_value = self.get_pv_value(pv)
        if pv_value in expected_values:
            return None
        else:
            return "Expected one of {expected}: actual {actual}".format(expected=expected_values, actual=pv_value)

    def wait_for(self, pv, timeout=30):
        """
        Wait for pv to be available or timeout and throw UnableToConnectToPVException.

        :param pv: pv to wait for
        :param timeout: time to wait for
        :return:
        :raises UnableToConnectToPVException: if pv can not be connected to after given time
        """
        if not self.ca.pv_exists(self._create_pv_with_prefix(pv), timeout=timeout):
            AssertionError("PV {pv} does not exist".format(pv=self._create_pv_with_prefix(pv)))

    def _create_pv_with_prefix(self, pv):
        """
        Create the full pv name with instrument prefix.

        :param pv: pv name without prefix
        :return: pv name with prefix
        """
        return "{prefix}{pv}".format(prefix=self.prefix, pv=pv)

    def _wait_for_pv_lambda(self, wait_for_lambda, timeout):
        """
        Wait for a lambda containing a pv to become None; return value or timeout and return actual value.

        :param wait_for_lambda: lambda we expect to be None
        :param timeout: time out period
        :return: final value of lambda
        """
        start_time = time.time()
        current_time = start_time

        while current_time - start_time < timeout:
            try:
                lambda_value = wait_for_lambda()
                if lambda_value is None:
                    return lambda_value
            except UnableToConnectToPVException:
                pass  # try again next loop maybe the PV will be up
            time.sleep(0.5)
            current_time = time.time()

        # last try
        return wait_for_lambda()

    def assert_pv_alarm_is(self, pv, alarm, timeout=5):
        """
        Assert that a pv is in alarm state given or timeout.

        :param pv: pv name
        :param alarm: alarm state (see constants ALARM_X)
        :param timeout: length of time to wait for change
        :return:
        :raises AssertionError: if alarm does not become requested value
        :raises UnableToConnectToPVException: if pv does not exist within timeout
        """

        self.assert_that_pv_is("{pv}.SEVR".format(pv=pv), alarm, timeout=timeout)
