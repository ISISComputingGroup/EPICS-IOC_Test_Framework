import functools
import unittest
from time import sleep

import six

from utils.ioc_launcher import IOCRegister, IocLauncher
from utils.emulator_launcher import EmulatorRegister, LewisLauncher


class ManagerMode(object):
    """A context manager for switching manager mode on."""
    MANAGER_MODE_PV = "CS:MANAGER"

    def __init__(self, channel_access):
        self.channel_access = channel_access
        self.channel_access.assert_that_pv_exists(self.MANAGER_MODE_PV)

    def __enter__(self):
        self.channel_access.set_pv_value(self.MANAGER_MODE_PV, 1)

    def __exit__(self, *args):
        self.channel_access.set_pv_value(self.MANAGER_MODE_PV, 0)


class _AssertLogContext(object):
    """A context manager used to implement assert_log_messages."""
    messages = list()
    first_message = 0

    def __init__(self, log_manager, number_of_messages=None, in_time=5, must_contain=None):
        """
        Args:
            log_manager: A reference to the IOC log object
            number_of_messages: A number of log messages to expect (None to not check number of messages)
            in_time: The amount of time to wait for messages to be generated
            must_contain: A string which must appear in the generated log messages (None to not check contents)
        """
        self.in_time = in_time
        self.log_manager = log_manager
        self.exp_num_of_messages = number_of_messages
        self.must_contain = must_contain

    def __enter__(self):
        self.log_manager.read_log()  # Read any excess log
        return self

    def __exit__(self, *args):
        sleep(self.in_time)
        self.messages = self.log_manager.read_log()

        actual_num_of_messages = len(self.messages)

        if self.exp_num_of_messages is not None and actual_num_of_messages != self.exp_num_of_messages:
            raise AssertionError("Incorrect number of log messages created. Expected {} and found {}"
                                 .format(self.exp_num_of_messages, actual_num_of_messages))

        if self.must_contain is not None and not any(self.must_contain in message for message in self.messages):
            raise AssertionError("Expected the generated log messages to contain the string '{}' but they didn't.\n"
                                 "The log messages were: \n{}".format(self.must_contain, "\n".join(self.messages)))

        return True


def get_running_lewis_and_ioc(emulator_name, ioc_name):
    """
    Assert that the emulator and ioc have been started if needed.

    :param emulator_name: the name of the lewis emulator; None for don't check the emulator
    :param ioc_name: the name of the IOC
    :return: lewis launcher and ioc launcher tuple
    :rtype: (LewisLauncher, IocLauncher)
    """
    lewis = EmulatorRegister.get_running(emulator_name)
    ioc = IOCRegister.get_running(ioc_name)

    if ioc is None and (lewis is None and emulator_name is not None):
        raise AssertionError("Emulator ({}) and IOC ({}) are not running".format(emulator_name, ioc_name))
    if ioc is None:
        raise AssertionError("IOC ({}) is not running".format(ioc_name))
    if lewis is None and emulator_name is not None:
        raise AssertionError("Emulator ({}) is not running".format(emulator_name))

    return lewis, ioc


def assert_log_messages(ioc, number_of_messages=None, in_time=1, must_contain=None):
    """
    A context object that asserts that the given code produces the given number of ioc log messages in the the given
    amount of time.

    To assert that only 5 messages are produced in 5 seconds::
        with assert_log_messages(self._ioc, 5, 5):
            do_something()

    The context manager will keep a reference to the messages themselves::
        with assert_log_messages(self._ioc, 5) as cm:
            do_something()

        self.assertEqual(cm.messages[0], "The first log message")

    Args:
        ioc (IocLauncher): The IOC that we are checking the logs for.
        number_of_messages (int): The number of messages that are expected (None to not check number of messages)
        in_time (int): The number of seconds to wait for messages
        must_contain (str): a string which must be contained in at least one of the messages (None to not check)
    """
    return _AssertLogContext(ioc.log_file_manager, number_of_messages, in_time, must_contain)


def skip_if_condition(condition, reason):
    """
    Decorator to skip tests given a particular condition.

    This is similar to unittest's @skipIf decorator, but this one determines it's condition at runtime as opposed to
    class load time. This is necessary because otherwise the decorators don't properly pick up changes in
    IOCRegister.uses_rec_sim

    Args:
        condition (func): The condition on which to skip the test. Should be callable.
        reason (str): The reason for skipping the test
    """
    def decorator(func):
        @six.wraps(func)
        def wrapper(*args, **kwargs):
            if condition():
                raise unittest.SkipTest(reason)
            func(*args, **kwargs)
        return wrapper
    return decorator


"""Decorator to skip tests if running in recsim."""
skip_if_recsim = functools.partial(skip_if_condition, lambda: IOCRegister.uses_rec_sim)

"""Decorator to skip tests if running in devsim"""
skip_if_devsim = functools.partial(skip_if_condition, lambda: not IOCRegister.uses_rec_sim)


def add_method(method):
    """
    Class decorator which as the method to the decorated class.

    This is inspired by https://stackoverflow.com/questions/9443725/add-method-to-a-class-dynamically-with-decorator
    and https://gist.github.com/victorlei/5968685.

    Args:
        method (func): The method to add to the class decorated. Should be callable.
    """

    @six.wraps(method)
    def wrapper(class_to_decorate):
        setattr(class_to_decorate, method.__name__, method)
        return class_to_decorate
    return wrapper


def parameterized_list(cases):
    """
    Creates a list of cases for parameterized to use to run tests.

    E.g.
    parameterized_list([1.3435, 12321, 1.0])
        = [("1.3435", 1.3435),("12321", 12321), ("1.0", 1.0)]

    Args:
         cases: List of cases to use in tests.

    Returns:
        list: list of tuples of where the first item is str(case).
    """

    return_list = []

    for case in cases:
        test_case = (str(case),)
        try:
            return_list.append(test_case + case)
        except TypeError:
            return_list.append(test_case + (case,))

    return return_list
