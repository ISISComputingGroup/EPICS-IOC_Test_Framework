import os
import subprocess

import sys

from utils.free_ports import get_free_ports
from utils.log_file import log_filename


class LewisRegister(object):
    """
    A way of registering running emulators
    """

    """static dictionary of running emulator"""
    RunningEmulators = {}

    @classmethod
    def get_running(cls, lewis_emulator):
        """
        Get a running emulator by name, return None if not running
        :param lewis_emulator: name of the lewis emulator to grab
        :return: lewis launcher
        """
        return cls.RunningEmulators.get(lewis_emulator)

    @classmethod
    def add_emulator(cls, name, emulator):
        """
        Add a emulator to the running list
        :param name: name of the emmulator
        :param emulator: the emmulator launcher
        :return:
        """
        cls.RunningEmulators[name] = emulator


class LewisNone(object):
    """
    Object representing a Lewis Launcher when Lewis is not required
    """

    def __init__(self, device):
        """

        :param device: device name
        """
        self.port = None
        self._device = device

    def __enter__(self):
        LewisRegister.add_emulator(self._device, self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def check(self):
        """
        The none lewis simulator is running
        :return: True
        """
        return True

    def backdoor_set_on_device(self, variable_name, value):
        """
        does nothing
        :param variable_name: name of the variable to set
        :param value: value
        :return:
        """
        pass


class LewisLauncher(object):
    """
    Launches Lewis.
    """

    def __init__(self, device, lewis_path, var_dir, lewis_protocol=None, lewis_additional_path=None, lewis_package=None):
        """
        Constructor that also launches Lewis.

        :param device: device to start
        :param lewis_path: path to lewis
        :param var_dir: location of directory to write log file and macros directories
        :param lewis_protocol: protocol to use; None let Lewis use the default protocol
        :param lewis_additional_path: additional path to add to lewis usually the location of the device emulators
        :param lewis_package: package to use by lewis
        """
        self._lewis_path = lewis_path
        self._lewis_protocol = lewis_protocol
        self._device = device
        self._process = None
        self._lewis_additional_path = lewis_additional_path
        self._lewis_package = lewis_package
        self.port = None
        self._logFile = None
        self._connected = None
        self._var_dir = var_dir

    def __enter__(self):
        self._open(self.port)
        LewisRegister.add_emulator(self._device, self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def _close(self):
        """
        Closes the Lewis session by killing the process.
        """
        print("Terminating Lewis")
        if self._process is not None:
            self._process.terminate()
        if self._logFile is not None:
            self._logFile.close()
            print "Lewis log written to {0}".format(self._log_filename())

    def _open(self, port):
        """
        Start the lewis emulator

        :param port: the port on which to run lewis
        :return:
        """

        self._control_port = str(get_free_ports(1)[0])
        lewis_command_line = [os.path.join(self._lewis_path, "lewis"),
                              "-r", "127.0.0.1:{control_port}".format(control_port=self._control_port)]
        if self._lewis_protocol is not None:
            lewis_command_line.extend(["-p", self._lewis_protocol])
        if self._lewis_additional_path is not None:
            lewis_command_line.extend(["-a", self._lewis_additional_path])
        if self._lewis_package is not None:
            lewis_command_line.extend(["-k", self._lewis_package])
        lewis_command_line.extend(
            ["-e", "100", self._device, "--", "--bind-address", "127.0.0.1", "--port", port])

        print("Starting Lewis")
        self._logFile = file(self._log_filename(), "w")
        self._logFile.write("Started Lewis with '{0}'\n".format(" ".join(lewis_command_line)))

        self._process = subprocess.Popen(lewis_command_line,
                                         creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         stdout=self._logFile,
                                         stderr=subprocess.STDOUT)
        self._connected = True

    def _log_filename(self):
        return log_filename("lewis", self._device, False, self._var_dir)

    def check(self):
        """
        Check that the lewis emmulator is running
        :return: True if it is running; False otherwise
        """
        if self._process.poll() is None:
            return True
        print "Lewis has terminated! It said:"
        stdoutdata, stderrdata = self._process.communicate()
        sys.stderr.write(stderrdata)
        sys.stdout.write(stdoutdata)
        return False

    def backdoor_set_on_device(self, variable_name, value):
        """
        Set a value in the device using the lewis backdoor
        :param variable_name: name of variable to set
        :param value: new value it should have
        :return:
        """
        if isinstance(value, str):
            self.backdoor_command(["device", str(variable_name), "'{0}'".format(value)])
        else:
            self.backdoor_command(["device", str(variable_name), str(value)])

    def backdoor_command(self, lewis_command):
        """
        Send a command to the backdoor of lewis
        :param lewis_command: array of command line arguments to send
        :return:
        """
        lewis_command_line = [
            os.path.join(self._lewis_path, "lewis-control.exe"),
            "-r", "127.0.0.1:{control_port}".format(control_port=self._control_port)]
        lewis_command_line.extend(lewis_command)
        self._logFile.write("lewis backdoor command: {0}\n".format(" ".join(lewis_command_line)))
        try:
            subprocess.check_call(lewis_command_line, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as ex:
            sys.stderr.write("Error using backdoor: {0}\n".format(ex.output))
            sys.stderr.write("Error code {0}\n".format(ex.returncode))
            raise ex

    def backdoor_emulator_disconnect_device(self):
        """
        Disconnect the emulated device
        :return:
        """
        if self._connected:
            self.backdoor_command(["simulation", "disconnect_device"])
        self._connected = False


    def backdoor_emulator_connect_device(self):
        """
        Connect the emulated device
        :return:
        """
        if not self._connected:
            self.backdoor_command(["simulation", "connect_device"])
        self._connected = True

