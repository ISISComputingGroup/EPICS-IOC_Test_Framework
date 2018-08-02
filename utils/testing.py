import functools
import unittest
from time import sleep

import six

from utils.ioc_launcher import IOCRegister, IocLauncher
from utils.lewis_launcher import LewisRegister, LewisLauncher


class _AssertLogContext(object):
    """A context manager used to implement assert_log_messages."""
    messages = list()
    first_message = 0

    def __init__(self, log_manager, number_of_messages, in_time):
        self.in_time = in_time
        self.log_manager = log_manager
        self.exp_num_of_messages = number_of_messages

    def __enter__(self):
        self.log_manager.read_log()  # Read any excess log
        return self

    def __exit__(self, *args):
        sleep(self.in_time)
        self.messages = self.log_manager.read_log()
        actual_num_of_messages = len(self.messages)

        if actual_num_of_messages != self.exp_num_of_messages:
            raise AssertionError("Incorrect number of log messages created. Expected {} and found {}"
                                 .format(self.exp_num_of_messages, actual_num_of_messages))

        return True


def get_running_lewis_and_ioc(emulator_name, ioc_name):
    """
    Assert that the emulator and ioc have been started if needed.

    :param emulator_name: the name of the lewis emulator; None for don't check the emulator
    :param ioc_name: the name of the IOC
    :return: lewis launcher and ioc launcher tuple
    :rtype: (LewisLauncher, IocLauncher)
    """
    lewis = LewisRegister.get_running(emulator_name)
    ioc = IOCRegister.get_running(ioc_name)

    if ioc is None and (lewis is None and emulator_name is not None):
        raise AssertionError("Emulator ({}) and IOC ({}) are not running".format(emulator_name, ioc_name))
    if ioc is None:
        raise AssertionError("IOC ({}) is not running".format(ioc_name))
    if lewis is None and emulator_name is not None:
        raise AssertionError("Emulator ({}) is not running".format(emulator_name))

    return lewis, ioc


def assert_log_messages(ioc, number_of_messages, in_time=1):
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
        number_of_messages (int): The number of messages that are expected
        in_time (int): The number of seconds to wait for messages
    """
    return _AssertLogContext(ioc.log_file_manager, number_of_messages, in_time)


def _skip_if_condition(condition, reason):
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
skip_if_recsim = functools.partial(_skip_if_condition, lambda: IOCRegister.uses_rec_sim)

"""Decorator to skip tests if running in devsim"""
skip_if_devsim = functools.partial(_skip_if_condition, lambda: not IOCRegister.uses_rec_sim)


def add_method(method):
    """
    Class decorator which as the method to the decorated class.

    This is inspired by https://stackoverflow.com/questions/9443725/add-method-to-a-class-dynamically-with-decorator
    and https://gist.github.com/victorlei/5968685.

    Args:
        method (func): The method to add to the class decorated.
    """

    @six.wraps(method)
    def wrapper(class_to_decorate):
        setattr(class_to_decorate, method.__name__, method)
        return class_to_decorate
    return wrapper
