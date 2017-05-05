import subprocess

import sys


class LewisNone(object):
    """
    Object representing a Lewis Launcher when Lewis is not required
    """

    def __init__(self):
        self.port = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def check(self):
        """
        The none lewis simulator is running
        :return: True
        """
        return True


class LewisLauncher(object):
    """
    Launches Lewis.
    """

    def __init__(self, device, lewis_path, lewis_protocol=None, lewis_additional_path=None, lewis_package=None):
        """
        Constructor that also launches Lewis.

        :param device: device to start
        :param lewis_path: path to lewis
        :param lewis_protocol: protocol to use; None let Lewis use the default protocol
        :param lewis_additional_path: additional path to add to lewis usually the location of the device emulators
        :param lewis_package: package to use by lewis
        """
        self._lewis_path = lewis_path
        self._lewis_protocol = lewis_protocol
        self._device = device
        self._proc = None
        self._lewis_additional_path = lewis_additional_path
        self._lewis_package = lewis_package
        self.port = None

    def __enter__(self):
        self._open(self.port)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def _close(self):
        """
        Closes the Lewis session by killing the process.
        """
        print("Terminating Lewis")
        if self._proc is not None:
            self._proc.terminate()

    def _open(self, port):
        """
        Start the lewis emulator

        :param port: the port on which to run lewis
        :return:
        """
        lewis_command_line = [self._lewis_path]
        if self._lewis_protocol is not None:
            lewis_command_line.extend(["-p", self._lewis_protocol])
        if self._lewis_additional_path is not None:
            lewis_command_line.extend(["-a", self._lewis_additional_path])
        if self._lewis_package is not None:
            lewis_command_line.extend(["-k", self._lewis_package])
        lewis_command_line.extend(
            ["-e", "100", self._device, "--", "--bind-address", "localhost", "--port", port])

        print("Starting Lewis")
        self._proc = subprocess.Popen(lewis_command_line,
                                      creationflags=subprocess.CREATE_NEW_CONSOLE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

    def check(self):
        if self._proc.poll() is None:
            return True
        print "Lewis has terminated! It said:"
        stdoutdata, stderrdata = self._proc.communicate()
        sys.stderr.write(stderrdata)
        sys.stdout.write(stdoutdata)
        return False
