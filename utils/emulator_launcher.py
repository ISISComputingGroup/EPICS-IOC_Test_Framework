"""
Lewis emulator interface classes.
"""
import abc
import os
import subprocess

import sys
from time import sleep, time
from functools import partial
import six

from utils.free_ports import get_free_ports
from utils.ioc_launcher import EPICS_TOP
from utils.log_file import log_filename
from utils.formatters import format_value

from utils.emulator_exceptions import UnableToConnectToEmulatorException


class EmulatorRegister(object):
    """
    A way of registering running emulators.
    """

    # Static dictionary of running emulators
    RunningEmulators = {}

    @classmethod
    def get_running(cls, name):
        """
        Get a running emulator by name, return None if not running.

        :param name: name of the lewis emulator to grab
        :return: lewis launcher
        """
        return cls.RunningEmulators.get(name)

    @classmethod
    def add_emulator(cls, name, emulator):
        """
        Add a emulator to the running list.

        :param name: name of the emmulator
        :param emulator: the emmulator launcher
        """
        cls.RunningEmulators[name] = emulator

    @classmethod
    def remove_emulator(cls, name):
        """
        Removes an emulator from the running list.

        :param name: name of the emmulator
        """
        del cls.RunningEmulators[name]


@six.add_metaclass(abc.ABCMeta)
class EmulatorLauncher(object):

    def __init__(self, device, var_dir, port, options):
        """
        Args:
            device: The name of the device to emulate
            var_dir: The directory in which to store logs
            port: The TCP port to listen on for connections
            options: Dictionary of any additional options required by specific launchers
        """
        self._device = device
        self._emulator_id = options.get("emulator_id", self._device)
        self._var_dir = var_dir
        self._port = port
        self._options = options

    def __enter__(self):
        self._open()
        EmulatorRegister.add_emulator(self._emulator_id, self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()
        EmulatorRegister.remove_emulator(self._emulator_id)

    def _get_device(self):
        return self._device

    def _get_var_dir(self):
        return self._var_dir

    @abc.abstractmethod
    def _close(self):
        """
        Close the emulator. This should perform any cleanup required to kill the emulator.
        """

    @abc.abstractmethod
    def _open(self):
        """
        Open the emulator. This should spawn the emulator process and return once the emulator is ready to
         accept commands.
        """

    @abc.abstractmethod
    def backdoor_get_from_device(self, variable, *args, **kwargs):
        """
        Get a value from  the device via the back door.

        Args:
            variable: The name of the variable to get
            args: arbitrary arguments
            kwargs: arbitrary keyword arguments

        Returns:
            The value returned via the backdoor
        """

    @abc.abstractmethod
    def backdoor_set_on_device(self, variable, value, *args, **kwargs):
        """
        Set a value from  the device via the back door.

        Args:
            variable: The name of the variable to set
            value: The value to set
            args: arbitrary arguments
            kwargs: arbitrary keyword arguments

        Returns:
            Nothing.
        """

    @abc.abstractmethod
    def backdoor_emulator_disconnect_device(self, *args, **kwargs):
        """
        Disconnect the device via the back door.

        Args:
            args: arbitrary arguments
            kwargs: arbitrary keyword arguments

        Returns:
            Nothing.
        """

    @abc.abstractmethod
    def backdoor_emulator_connect_device(self, *args, **kwargs):
        """
        Connect the device via the back door.

        Args:
            args: arbitrary arguments
            kwargs: arbitrary keyword arguments

        Returns:
            Nothing.
        """

    @abc.abstractmethod
    def backdoor_run_function_on_device(self, *args, **kwargs):
        """
        Runs a function on an emulator via the backdoor.

        Args:
            args: arbitrary arguments
            kwargs: arbitrary keyword arguments

        Returns:
            Nothing.
        """

    def assert_that_emulator_value_is(self, emulator_property, expected_value, timeout=None, message=None,
                                      cast=lambda val: val):
        """
        Assert that the emulator property has the expected value or that it becomes the expected value within the
        timeout.

        Args:
            emulator_property (string): emulator property to check
            expected_value: expected value. Emulator backdoor always returns a string, so the value should be a string.
            timeout (float): if it hasn't changed within this time raise assertion error
            message (string): Extra message to print
            cast (callable): function which casts the returned value to an appropriate type before
                checking equality. E.g. to cast to float pass the float class as this argument.
        Raises:
            AssertionError: if emulator property is not the expected value
            UnableToConnectToPVException: if emulator property does not exist within timeout
        """

        if message is None:
            message = "Expected PV to have value {}.".format(format_value(expected_value))

        return self.assert_that_emulator_value_causes_func_to_return_true(
            emulator_property, lambda val: cast(val) == expected_value, timeout=timeout, msg=message)

    def assert_that_emulator_value_causes_func_to_return_true(
            self, emulator_property, func, timeout=None, msg=None):
        """
        Check that an emulator property satisfies a given function within some timeout.

        Args:
            emulator_property (string): emulator property to check
            func: a function that takes one argument, the emulator property value, and returns True if the value is
                valid.
            timeout: time to wait for the PV to satisfy the function
            msg: custom message to print on failure
        Raises:
            AssertionError: If the function does not evaluate to true within the given timeout
        """

        def wrapper(msg):
            value = self.backdoor_get_from_device(emulator_property)
            try:
                return_value = func(value)
            except Exception as e:
                return "Exception was thrown while evaluating function '{}' on emulator property {}. " \
                       "Exception was: {} {}".format(func.__name__,
                                                     format_value(value), e.__class__.__name__, e.message)
            if return_value:
                return None
            else:
                return "{}{}{}".format(msg, os.linesep, "Final emulator property value was {}"
                                       .format(format_value(value)))

        if msg is None:
            msg = "Expected function '{}' to evaluate to True when reading emulator property '{}'." \
                .format(func.__name__, emulator_property)

        err = self._wait_for_emulator_lambda(partial(wrapper, msg), timeout)

        if err is not None:
            raise AssertionError(err)

    def _wait_for_emulator_lambda(self, wait_for_lambda, timeout):
        """
        Wait for a lambda containing a emulator property to become None; return value or timeout and return actual value.

        Args:
            wait_for_lambda: lambda we expect to be None
            timeout: time out period
        Returns:
            final value of lambda
        """
        start_time = time()
        current_time = start_time

        if timeout is None:
            timeout = self._default_timeout

        while current_time - start_time < timeout:
            try:
                lambda_value = wait_for_lambda()
                if lambda_value is None:
                    return lambda_value
            except UnableToConnectToEmulatorException:
                pass  # try again next loop maybe the emulator property will have changed

            sleep(0.5)
            current_time = time()

        # last try
        return wait_for_lambda()

    def assert_that_emulator_value_is_greater_than(self, emulator_property, min_value, timeout=None):
            """
            Assert that an emulator property has a value greater than the expected value.

            Args:
                 emulator_property (string): Name of the numerical emulator property.
                 min_value (float): Minimum value (inclusive).Emulator backdoor always returns a string, so the value
                 should be a string.
                 timeout: if it hasn't changed within this time raise assertion error
            Raises:
                 AssertionError: if value does not become requested value
                 UnableToConnectToPVException: if pv does not exist within timeout
            """

            message = "Expected emulator property {} to have a value greater than or equal to {}".format(
                emulator_property, min_value)
            return self.assert_that_emulator_value_causes_func_to_return_true(
                emulator_property, lambda value: min_value <= float(value), timeout, message)


class NullEmulatorLauncher(EmulatorLauncher):
    """
    A null emulator launcher that does nothing.
    """

    def _open(self): pass

    def _close(self): pass

    def backdoor_get_from_device(self, variable, *args, **kwargs): return None

    def backdoor_set_on_device(self, variable, value, *args, **kwargs): pass

    def backdoor_emulator_disconnect_device(self, *args, **kwargs): pass

    def backdoor_emulator_connect_device(self, *args, **kwargs): pass

    def backdoor_run_function_on_device(self, *args, **kwargs): pass


class LewisLauncher(EmulatorLauncher):
    """
    Launches Lewis.
    """

    _DEFAULT_PY_PATH = os.path.join("C:\\", "Instrument", "Apps", "Python")
    _DEFAULT_LEWIS_PATH = os.path.join(_DEFAULT_PY_PATH, "scripts")

    def __init__(self, device, var_dir, port, options):
        """
        Constructor that also launches Lewis.

        Args:
            device: device to start
            var_dir: location of directory to write log file and macros directories
            port: the port to use
        """
        super(LewisLauncher, self).__init__(device, var_dir, port, options)

        self._lewis_path = options.get("lewis_path", LewisLauncher._DEFAULT_LEWIS_PATH)
        self._python_path = options.get("python_path", os.path.join(LewisLauncher._DEFAULT_PY_PATH, "python.exe"))
        self._lewis_protocol = options.get("lewis_protocol", "stream")
        self._lewis_additional_path = options.get("lewis_additional_path",
                                                  os.path.join(EPICS_TOP, "support", "DeviceEmulator", "master"))
        self._lewis_package = options.get("lewis_package", "lewis_emulators")
        self._default_timeout = options.get("default_timeout", 5)

        self._process = None
        self._logFile = None
        self._connected = None

    def _close(self):
        """
        Closes the Lewis session by killing the process.
        """
        print("Terminating Lewis")
        if self._process is not None:
            self._process.terminate()
        if self._logFile is not None:
            self._logFile.close()
            print("Lewis log written to {0}".format(self._log_filename()))

    def _open(self):
        """
        Start the lewis emulator.

        :param port: the port on which to run lewis
        :return:
        """

        self._control_port = str(get_free_ports(1)[0])
        lewis_command_line = [self._python_path, os.path.join(self._lewis_path, "lewis.exe"),
                              "-r", "127.0.0.1:{control_port}".format(control_port=self._control_port)]
        lewis_command_line.extend(["-p", "{protocol}: {{bind_address: 127.0.0.1, port: {port}}}"
                                  .format(protocol=self._lewis_protocol, port=self._port)])
        if self._lewis_additional_path is not None:
            lewis_command_line.extend(["-a", self._lewis_additional_path])
        if self._lewis_package is not None:
            lewis_command_line.extend(["-k", self._lewis_package])
        lewis_command_line.extend(["-e", "100", self._device])

        print("Starting Lewis")
        self._logFile = open(self._log_filename(), "w")
        self._logFile.write("Started Lewis with '{0}'\n".format(" ".join(lewis_command_line)))

        self._process = subprocess.Popen(lewis_command_line,
                                         creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         stdout=self._logFile,
                                         stderr=subprocess.STDOUT)
        self._connected = True

    def _log_filename(self):
        return log_filename("lewis", self._emulator_id, False, self._var_dir)

    def check(self):
        """
        Check that the lewis emulator is running.

        :return: True if it is running; False otherwise
        """
        if self._process.poll() is None:
            return True
        print("Lewis has terminated! It said:")
        stdoutdata, stderrdata = self._process.communicate()
        sys.stderr.write(stderrdata)
        sys.stdout.write(stdoutdata)
        return False

    def _convert_to_string_for_backdoor(self, value):
        """
        Convert the value given to a string for the backdoor. If the type is a string suround with quotes otherwise
        pass it raw, e.g. for a number.
        Args:
            value: value to convert

        Returns: value as a string for the backdoor

        """
        return "'{}'".format(value) if isinstance(value, str) else str(value)

    def backdoor_set_on_device(self, variable_name, value, *_, **__):
        """
        Set a value in the device using the lewis backdoor.

        :param variable_name: name of variable to set
        :param value: new value it should have
        :return:
        """
        self.backdoor_command(["device", str(variable_name), self._convert_to_string_for_backdoor(value)])

    def backdoor_run_function_on_device(self, function_name, arguments=None):
        """
        Run a function in lewis using the back door on a device.

        :param function_name: name of the function to call
        :param arguments: an iterable of the arguments for the function; None means no arguments. Arguments will
            automatically be turned into json
        :return:
        """
        command = ["device", function_name]
        if arguments is not None:
            command.extend([self._convert_to_string_for_backdoor(argument) for argument in arguments])

        return self.backdoor_command(command)

    def backdoor_command(self, lewis_command):
        """
        Send a command to the backdoor of lewis.

        :param lewis_command: array of command line arguments to send
        :return: lines from the command output
        """
        lewis_command_line = [self._python_path, os.path.join(self._lewis_path, "lewis-control.exe"),
                              "-r", "127.0.0.1:{control_port}".format(control_port=self._control_port)]
        lewis_command_line.extend(lewis_command)
        self._logFile.write("lewis backdoor command: {0}\n".format(" ".join(lewis_command_line)))
        try:
            p = subprocess.Popen(lewis_command_line, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            for i in range(1, 30):
                code = p.poll()
                if code == 0:
                    break
                sleep(0.1)
            else:
                p.terminate()
                print("Lewis backdoor did not finish!")
            return [line.strip() for line in p.stdout]
        except subprocess.CalledProcessError as ex:
            sys.stderr.write("Error using backdoor: {0}\n".format(ex.output))
            sys.stderr.write("Error code {0}\n".format(ex.returncode))
            raise ex

    def backdoor_emulator_disconnect_device(self):
        """
        Disconnect the emulated device.

        :return:
        """
        if self._connected:
            self.backdoor_command(["simulation", "disconnect_device"])
        self._connected = False

    def backdoor_emulator_connect_device(self):
        """
        Connect the emulated device.

        :return:
        """
        if not self._connected:
            self.backdoor_command(["simulation", "connect_device"])
        self._connected = True

    def backdoor_get_from_device(self, variable_name, *_, **__):
        """
        Return the string of a value on a device from lewis.
        :param variable_name: name of the variable
        :return: the variables value, as a string
        """
        return "".join(self.backdoor_command(["device", str(variable_name)]))


class CommandLineEmulatorLauncher(EmulatorLauncher):

    def __init__(self, device, var_dir, port, options):
        super(CommandLineEmulatorLauncher, self).__init__(device, var_dir, port, options)
        try:
            self.command_line = options["emulator_command_line"]
        except KeyError:
            raise KeyError("To use a command line emulator launcher, the 'emulator_command_line' option must be "
                           "provided as part of the options dictionary")

        try:
            self.wait = options["emulator_wait_to_finish"]
        except KeyError:
            self.wait = False

        self._process = None
        self._log_file = None

    def _open(self):
        self._log_file = open(log_filename("cmdemulator", self._device, True, self._var_dir), "w")
        self._call_command_line(self.command_line.format(port=self._port))

    def _call_command_line(self, command_line):
        self._process = subprocess.Popen(command_line,
                                         creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         stdout=self._log_file,
                                         stderr=subprocess.STDOUT)

        if self.wait:
            self._process.wait()

    def _close(self):
        if self._process is not None:
            self._process.terminate()
        if self._log_file is not None:
            self._log_file.close()

    def backdoor_get_from_device(self, variable, *args, **kwargs):
        raise ValueError("Cannot use backdoor for an arbitrary command line launcher")

    def backdoor_set_on_device(self, variable, value, *args, **kwargs):
        raise ValueError("Cannot use backdoor for an arbitrary command line launcher")

    def backdoor_emulator_disconnect_device(self, *args, **kwargs):
        raise ValueError("Cannot use backdoor for an arbitrary command line launcher")

    def backdoor_emulator_connect_device(self, *args, **kwargs):
        raise ValueError("Cannot use backdoor for an arbitrary command line launcher")

    def backdoor_run_function_on_device(self, *args, **kwargs):
        raise ValueError("Cannot use backdoor for an arbitrary command line launcher")


class BeckhoffEmulatorLauncher(CommandLineEmulatorLauncher):

    def __init__(self, device, var_dir, port, options):
        try:
            self.beckhoff_root = options["beckhoff_root"]
            self.solution_path = options["solution_path"]
        except KeyError:
            raise KeyError("To use a beckhoff emulator launcher, the 'beckhoff_root' and `solution_path` options must"
                           " be provided as part of the options dictionary")

        automation_tools_dir = os.path.join(self.beckhoff_root, "util_scripts", "AutomationTools")
        automation_tools_binary = os.path.join(automation_tools_dir, "bin", "x64", "Release", "AutomationTools.exe")

        if os.path.exists(automation_tools_binary):
            plc_to_start = os.path.join(self.beckhoff_root, self.solution_path)
            self.beckhoff_command_line = '{} "{}" '.format(automation_tools_binary, plc_to_start)
            self.startup_command = self.beckhoff_command_line + "activate run " + options.get("plc_name", "")

            options["emulator_command_line"] = self.startup_command
            options["emulator_wait_to_finish"] = True
            super(BeckhoffEmulatorLauncher, self).__init__(device, var_dir, port, options)
        else:
            raise IOError("Unable to find AutomationTools.exe. Hint: You must build the solution located at:"
                          " {} \n".format(automation_tools_dir))
