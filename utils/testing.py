import functools
import unittest
from time import sleep
from types import TracebackType
from typing import TYPE_CHECKING, Callable, Concatenate, ParamSpec, Self, Type, TypeVar, overload

from utils.emulator_launcher import EmulatorRegister
from utils.ioc_launcher import IOCRegister
from utils.test_modes import TestModes

P = ParamSpec("P")
T = TypeVar("T")
CT = TypeVar("CT")

if TYPE_CHECKING:
    from utils.channel_access import ChannelAccess
    from utils.emulator_launcher import EmulatorLauncher, MultiLewisLauncher
    from utils.ioc_launcher import BaseLauncher, IocLauncher
    from utils.log_file import LogFileManager


class ManagerMode(object):
    """A context manager for switching manager mode on."""

    MANAGER_MODE_PV = "CS:MANAGER"

    def __init__(self, channel_access: "ChannelAccess") -> None:
        self.channel_access = channel_access
        self.channel_access.assert_that_pv_exists(self.MANAGER_MODE_PV)

    def __enter__(self) -> None:
        self.channel_access.set_pv_value(self.MANAGER_MODE_PV, 1)
        self.channel_access.assert_that_pv_is(self.MANAGER_MODE_PV, "Yes", timeout=5)

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.channel_access.set_pv_value(self.MANAGER_MODE_PV, 0)
        self.channel_access.assert_that_pv_is(self.MANAGER_MODE_PV, "No", timeout=5)


class _AssertLogContext(object):
    """A context manager used to implement assert_log_messages."""

    messages = []
    first_message = 0

    def __init__(
        self,
        log_manager: "LogFileManager",
        number_of_messages: int | None = None,
        in_time: float = 5,
        must_contain: str | None = None,
        ignore_log_client_failures: bool = True,
        ignore_autosave: bool = True,
    ) -> None:
        """
        Args:
            log_manager: A reference to the IOC log object
            number_of_messages: A number of log messages to expect (None to not check number of
                messages)
            in_time: The amount of time to wait for messages to be generated
            must_contain: A string which must appear in the generated log messages (None to not
                check contents)
            ignore_log_client_failures (bool): Whether to ignore messages about not being able to
                connect to logserver
            ignore_autosave (bool): Whether to ignore messages coming from autosave
        """
        self.in_time = in_time
        self.log_manager = log_manager
        self.exp_num_of_messages = number_of_messages
        self.must_contain = must_contain
        self.ignore_log_client_failures = ignore_log_client_failures
        self.ignore_autosave = ignore_autosave

    def __enter__(self) -> Self:
        self.log_manager.read_log()  # Read any excess log
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        sleep(self.in_time)
        self.messages = self.log_manager.read_log()

        if self.ignore_log_client_failures:
            self.messages = [message for message in self.messages if "log client: " not in message]

        if self.ignore_autosave:
            self.messages = [
                message
                for message in self.messages
                if "autosave" not in message and "save_restore" not in message
            ]

        actual_num_of_messages = len(self.messages)

        if (
            self.exp_num_of_messages is not None
            and actual_num_of_messages > self.exp_num_of_messages
        ):
            raise AssertionError(
                "Incorrect number of log messages created. Expected {} and found {}.\n"
                "Found log messages were: \n{}".format(
                    self.exp_num_of_messages, actual_num_of_messages, "\n".join(self.messages)
                )
            )

        if self.must_contain is not None and not any(
            self.must_contain in message for message in self.messages
        ):
            raise AssertionError(
                "Expected the generated log messages to contain the string '{}' but they didn't.\n"
                "The log messages were: \n{}".format(self.must_contain, "\n".join(self.messages))
            )

        return True


@overload
def get_running_lewis_and_ioc(
    emulator_name: None, ioc_name: str
) -> tuple[None, "BaseLauncher"]: ...


@overload
def get_running_lewis_and_ioc(
    emulator_name: str, ioc_name: str
) -> tuple["EmulatorLauncher | MultiLewisLauncher", "BaseLauncher"]: ...


def get_running_lewis_and_ioc(
    emulator_name: str | None = None, ioc_name: str | None = None
) -> tuple["EmulatorLauncher | MultiLewisLauncher | None", "BaseLauncher"]:
    """
    Assert that the emulator and ioc have been started if needed.

    :param emulator_name: the name of the lewis emulator; None for don't check the emulator
    :param ioc_name: the name of the IOC
    :return: lewis launcher and ioc launcher tuple
    """
    lewis = EmulatorRegister.get_running(emulator_name)
    ioc = IOCRegister.get_running(ioc_name)

    if ioc is None and (lewis is None and emulator_name is not None):
        raise AssertionError(
            "Emulator ({}) and IOC ({}) are not running".format(emulator_name, ioc_name)
        )
    if ioc is None:
        raise AssertionError("IOC ({}) is not running".format(ioc_name))
    if lewis is None and emulator_name is not None:
        raise AssertionError("Emulator ({}) is not running".format(emulator_name))

    return lewis, ioc


def assert_log_messages(
    ioc: "IocLauncher",
    number_of_messages: int | None = None,
    in_time: float = 1,
    must_contain: str | None = None,
    ignore_log_client_failures: bool = True,
    ignore_autosave: bool = True,
) -> _AssertLogContext:
    """
    A context object that asserts that the given code produces the given number of ioc log messages
    in the the given amount of time.

    To assert that no more than 5 messages are produced in 5 seconds::
        with assert_log_messages(self._ioc, 5, 5):
            do_something()

    The context manager will keep a reference to the messages themselves::
        with assert_log_messages(self._ioc, 5) as cm:
            do_something()

        self.assertEqual(cm.messages[0], "The first log message")

    Args:
        ioc (IocLauncher): The IOC that we are checking the logs for.
        number_of_messages (int): The maximum number of messages that are expected (None to not
            check number of messages)
        in_time (int): The number of seconds to wait for messages
        must_contain (str): a string which must be contained in at least one of the messages (None
            to not check)
        ignore_log_client_failures (bool): Whether to ignore messages about not being able to
            connect to logserver
        ignore_autosave (bool): Whether to ignore messages coming from autosave
    """
    manager = ioc.log_file_manager
    if manager is None:
        raise ValueError("IOC does not have a log file manager, cannot use assert_log_messages")
    return _AssertLogContext(
        manager,
        number_of_messages,
        in_time,
        must_contain,
        ignore_log_client_failures,
        ignore_autosave,
    )


def skip_if_condition(
    condition: Callable[[], bool], reason: str
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to skip tests given a particular condition.

    This is similar to unittest's @skipIf decorator, but this one determines it's condition at
    runtime as opposed to class load time. This is necessary because otherwise the decorators don't
    properly pick up changes in IOCRegister.uses_rec_sim

    Args:
        condition (func): The condition on which to skip the test. Should be callable.
        reason (str): The reason for skipping the test
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if condition():
                raise unittest.SkipTest(reason)
            return func(*args, **kwargs)

        return wrapper

    return decorator


"""Decorator to skip tests if running in recsim."""
skip_if_recsim = functools.partial(skip_if_condition, lambda: IOCRegister.uses_rec_sim)

"""Decorator to skip tests if running in devsim"""
skip_if_devsim = functools.partial(
    skip_if_condition, lambda: IOCRegister.test_mode == TestModes.DEVSIM
)

"""Decorator to skip tests if running in nosim"""
skip_if_nosim = functools.partial(
    skip_if_condition, lambda: IOCRegister.test_mode == TestModes.NOSIM
)

"""Decorator to skip tests if running in devsim"""
skip_always = functools.partial(skip_if_condition, lambda: True)


def add_method(method: Callable[P, T]) -> Callable[[Type[CT]], Type[CT]]:
    """
    Class decorator which adds the method to the decorated class.

    This is inspired by
    https://stackoverflow.com/questions/9443725/add-method-to-a-class-dynamically-with-decorator
    and
    https://gist.github.com/victorlei/5968685.

    Args:
        method (func): The method to add to the class decorated. Should be callable.
    """

    def wrapper(class_to_decorate: Type[CT]) -> Type[CT]:
        setattr(class_to_decorate, method.__name__, method)
        return class_to_decorate

    return wrapper


def parameterized_list(cases: list[T]) -> list[tuple[str, T]]:
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
            return_list.append(test_case + case)  # type: ignore
        except TypeError:
            return_list.append(test_case + (case,))

    return return_list


def unstable_test(
    max_retries: int = 2,
    error_class: Type[BaseException] | tuple[Type[BaseException], ...] = AssertionError,
    wait_between_runs: float = 0,
) -> Callable[
    [Callable[Concatenate[unittest.TestCase, P], T]], Callable[Concatenate[unittest.TestCase, P], T]
]:
    """
    Decorator which will retry a test on failure. This decorator should not be required on most
    tests and should not be included as standard when writing a test.

    Args:
        max_retries: the max number of times to run the test before actually throwing an error
            (defaults to 2 retries)
        error_class: the class of error to retry under (defaults to AssertionError)
        wait_between_runs: number of seconds to wait between each failed attempt at running the test
    """

    def decorator(
        func: Callable[Concatenate[unittest.TestCase, P], T],
    ) -> Callable[Concatenate[unittest.TestCase, P], T]:
        @functools.wraps(func)
        def wrapper(self: unittest.TestCase, *args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(self, *args, **kwargs)  # Initial attempt to run the test "normally"
            except error_class:
                last_error = None
                for _ in range(max_retries):
                    sleep(wait_between_runs)
                    try:
                        self.setUp()  # Need to rerun setup
                        return func(self, *args, **kwargs)
                    except error_class as e:
                        last_error = e
                    finally:
                        self.tearDown()  # Rerun tearDown regardless of success or not
                else:
                    raise last_error

        return wrapper

    return decorator
