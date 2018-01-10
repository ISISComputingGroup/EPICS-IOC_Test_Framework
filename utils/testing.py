import functools
import unittest

from utils.ioc_launcher import IOCRegister, IocLauncher
from utils.lewis_launcher import LewisRegister, LewisLauncher


def get_running_lewis_and_ioc(emulator_name, ioc_name):
    """
    Assert that the emulator and ioc have been started if needed.

    :param emulator_name: the name of the lewis emulator
    :param ioc_name: the name of the IOC
    :return: lewis launcher and ioc launcher tuple
    :rtype: (LewisLauncher, IocLauncher)
    """
    lewis = LewisRegister.get_running(emulator_name)
    ioc = IOCRegister.get_running(ioc_name)

    if ioc is None and lewis is None:
        raise AssertionError("Emulator ({}) and IOC ({}) are not running".format(emulator_name, ioc_name))
    if ioc is None:
        raise AssertionError("IOC ({}) is not running".format(ioc_name))
    if lewis is None:
        raise AssertionError("Emulator ({}) is not running".format(emulator_name))

    return lewis, ioc


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
        @functools.wraps(func)
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
