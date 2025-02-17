"""
Code that launches an IOC/application under test
"""

import abc
import os
import subprocess
import telnetlib
import time
from abc import ABCMeta
from contextlib import contextmanager
from datetime import date
from signal import SIGTERM
from time import sleep
from types import TracebackType
from typing import Any, Callable, Generator, Self, Type

import psutil

from utils.channel_access import ChannelAccess
from utils.free_ports import get_free_ports
from utils.log_file import LogFileManager, log_filename
from utils.test_modes import TestModes

APPS_BASE = os.path.join("C:\\", "Instrument", "Apps")
EPICS_TOP = os.environ.get("EPICS_KIT_ROOT", os.path.join(APPS_BASE, "EPICS"))
IOCS_DIR = os.path.join(EPICS_TOP, "ioc", "master")
PYTHON3 = os.environ.get("PYTHON3", os.path.join(APPS_BASE, "Python3", "python.exe"))

DEFAULT_IOC_START_TEXT = "epics>"
# DEFAULT_IOC_START_TEXT = "iocRun: All initialization complete"

MAX_TIME_TO_WAIT_FOR_IOC_TO_START = 120

EPICS_CASE_ENVIRONMENT_VARS = {
    "EPICS_CAS_INTF_ADDR_LIST": "127.0.0.1",
    "EPICS_CAS_BEACON_ADDR_LIST": "127.255.255.255",
}


def get_default_ioc_dir(iocname: str, iocnum: int = 1) -> str:
    """
    Gets the default path to run the IOC given the name.
    Args:
        iocname: the name of the ioc
        iocnum: the number of the ioc to start (defaults to 1)
    Returns:
        the path
    """
    return os.path.join(
        EPICS_TOP, "ioc", "master", iocname, "iocBoot", "ioc{}-IOC-{:02d}".format(iocname, iocnum)
    )


class CheckExistencePv(object):
    """
    Checks to see if a IOC has been started correctly by asserting that a pv does not exist on entry
    and does on exit

    Args:
        ca: channel access
        device: the device
        test_pv: the name of the test pv, defaults to the DISABLE PV
    """

    def __init__(self, ca: ChannelAccess, device: str, test_pv: str = "DISABLE") -> None:
        self.ca = ca
        self.device = device
        self.test_pv = test_pv

    def __enter__(self) -> None:
        if self.test_pv is None:
            print("No existence PV specified.")
            return

        try:
            print("Check that IOC is not running")
            self.ca.assert_that_pv_does_not_exist(self.test_pv)
        except AssertionError as ex:
            raise AssertionError(
                "IOC '{}' appears to already be running: {}".format(self.device, ex)
            )

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.test_pv is None:
            return

        try:
            self.ca.assert_that_pv_exists(self.test_pv)
        except AssertionError as ex:
            full_pv = self.ca.create_pv_with_prefix(self.test_pv)
            raise AssertionError(
                "PV '{}' still does not exist after IOC start: {}".format(full_pv, ex)
            )


class IOCRegister(object):
    """
    A way of registering running iocs.
    """

    # Static dictionary of running iocs
    RunningIOCs: dict[str, "BaseLauncher"] = {}

    uses_rec_sim = False
    test_mode = TestModes.DEVSIM

    @classmethod
    def get_running(cls, ioc_name: str | None) -> "BaseLauncher | None":
        """
        Get a running ioc by name, return None if not running.

        :param ioc_name: name of the ioc emulator to grab
        :return: ioc launcher
        """
        if ioc_name is None:
            return None
        return cls.RunningIOCs.get(ioc_name)

    @classmethod
    def add_ioc(cls, name: str, ioc: "BaseLauncher") -> None:
        """
        Add an ioc to the running list.

        :param name: name of the ioc
        :param ioc: the ioc launcher
        :return:
        """
        cls.RunningIOCs[name] = ioc


class BaseLauncher(object, metaclass=ABCMeta):
    """
    Launcher base, this is the base class for a launcher of application under test.
    """

    def __init__(
        self, test_name: str, ioc_config: dict[str, Any], test_mode: TestModes, var_dir: str
    ) -> None:
        """
        Constructor which picks some generic things out of the config.
        Args:
            test_name: name of test we are running.
            ioc_config: Dictionary containing
                 name: String, Device name
                 directory: String, the directory where st.cmd for the IOC is found
                 custom_prefix: String, the prefix for the IOC PVs, default of IOC name
                 started_text: String, the text printed when the IOC has started, default of
                    DEFAULT_IOC_START_TEXT
                 pv_for_existence: String, the PV to check for whether the IOC is running, default
                    of DISABLE
                 macros: Dict, the macros that should be passed to this IOC
            var_dir: The directory into which the launcher will save log files.
        """
        self._device = ioc_config["name"]
        self._device_icp_config_name = ioc_config.get("icpconfigname", ioc_config["name"])
        self._directory = ioc_config["directory"]
        self._prefix = ioc_config.get("custom_prefix", self._device)
        self._ioc_started_text = ioc_config.get("started_text", DEFAULT_IOC_START_TEXT)
        self._pv_for_existence = ioc_config.get("pv_for_existence", "DISABLE")
        self.macros = ioc_config.get("macros", {})
        self.emulator_port = int(self.macros["EMULATOR_PORT"])
        self._extra_environment_vars = ioc_config.get("environment_vars", {})
        self._init_values = ioc_config.get("inits", {})
        self._delay_after_startup = ioc_config.get("delay_after_startup", 0)
        self._var_dir = var_dir
        self._test_name = test_name
        self.ca = None
        self.command_line: list[str] = []
        self.log_file_manager = None
        self._process = None
        self._test_mode = test_mode

        if test_mode not in [TestModes.RECSIM, TestModes.DEVSIM, TestModes.NOSIM]:
            raise ValueError("Invalid test mode provided")

        self.use_rec_sim = test_mode == TestModes.RECSIM
        IOCRegister.uses_rec_sim = self.use_rec_sim
        IOCRegister.test_mode = self._test_mode

        self.log_file_name = log_filename(
            self._test_name, "ioc", self._device, self._test_mode, self._var_dir
        )

    def open(self) -> None:
        """
        Starts the application under test.
        """
        self.command_line = self._command_line()

        st_cmd_path = os.path.join(self._directory, "st.cmd")

        if not os.path.isfile(st_cmd_path):
            print("St.cmd path not found: '{0}'".format(st_cmd_path))

        ca = self._get_channel_access()

        with CheckExistencePv(ca, self._device, self._pv_for_existence):
            print(f"Starting IOC ({self._device}), IOC log file is {self.log_file_name}")

            settings = self.get_environment_vars()

            self.create_macros_file()

            self.log_file_manager = LogFileManager(self.log_file_name)
            self.log_file_manager.log_file_w.write(
                "Started IOC with '{0}'".format(" ".join(self.command_line))
            )

            # To be able to see the IOC output for debugging, remove the redirection of stdin,
            # stdout and stderr.
            # This does mean that the IOC will need to be closed manually after the tests.
            # Make sure to revert before checking code in
            self._process = subprocess.Popen(
                " ".join(self.command_line),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=self._directory,
                stdin=subprocess.PIPE,
                stdout=self.log_file_manager.log_file_w,
                stderr=subprocess.STDOUT,
                env=settings,
            )

            # Write a return so that an epics terminal will appear after boot
            stdin = self._process.stdin
            assert stdin is not None
            stdin.write("\n".encode("utf-8"))
            stdin.flush()
            self.log_file_manager.wait_for_console(
                MAX_TIME_TO_WAIT_FOR_IOC_TO_START, self._ioc_started_text
            )

            for key, value in self._init_values.items():
                print("Initialising PV {} to {}".format(key, value))
                ca.set_pv_value(key, value)

        IOCRegister.add_ioc(self._device, self)

        sleep(self._delay_after_startup)

    @abc.abstractmethod
    def _command_line(self) -> list[str]:
        """
        The command line used to start an IOC that a subclass is expected to provide.
        """

    def close(self) -> None:
        """
        Exits the application under test
        """
        pass

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _get_channel_access(self) -> ChannelAccess:
        """
        :return (ChannelAccess): the channel access component
        """
        if self.ca is None:
            self.ca = ChannelAccess(device_prefix=self._prefix)

        return self.ca

    def create_macros_file(self) -> None:
        """
        Creates a temporary file that sets the EPICS macros, this file is called when the IOC first
        starts
        """
        full_dir = os.path.join(self._var_dir, "tmp")
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)

        with open(os.path.join(full_dir, "test_macros.txt"), mode="w") as f:
            for macro, value in self.macros.items():
                f.write(
                    '{ioc_name}__{macro}="{value}"\n'.format(
                        ioc_name=self._device_icp_config_name, macro=macro, value=value
                    )
                )

    def get_environment_vars(self) -> dict[str, str]:
        """
        Get the current environment variables and add in the extra ones needed for starting the IOC
        in DEVSIM/RECSIM.
        :return: (Dict): The names and values of the environment variables.
        """
        settings = os.environ.copy()
        if self._test_mode == TestModes.RECSIM:
            # Using record simulation
            settings["TESTDEVSIM"] = ""
            settings["TESTRECSIM"] = "yes"
            settings["TESTNOSIM"] = ""
        elif self._test_mode == TestModes.DEVSIM:
            # Not using record simulation
            settings["TESTDEVSIM"] = "yes"
            settings["TESTRECSIM"] = ""
            settings["TESTNOSIM"] = ""
        else:
            # real hardware
            settings["TESTDEVSIM"] = ""
            settings["TESTRECSIM"] = ""
            settings["TESTNOSIM"] = "yes"

        # Set the port
        settings["EMULATOR_PORT"] = str(self.emulator_port)

        for env_name, setting in self._extra_environment_vars.items():
            settings[env_name] = setting

        return settings

    def set_simulated_value(self, pv_name: str, value: float | int | str | bool) -> None:
        """
        If this IOC is in rec sim set the PV value.

        :param pv_name: name of the pv value
        :param value: value to set
        :return:
        """
        if self.use_rec_sim:
            self._get_channel_access().set_pv_value(pv_name, value)


class ProcServLauncher(BaseLauncher):
    """
    Launches an IOC from procServ.exe
    """

    ICPTOOLS = os.path.join(EPICS_TOP, "tools", "master")

    def __init__(
        self, test_name: str, ioc: dict[str, Any], test_mode: TestModes, var_dir: str
    ) -> None:
        """
        Constructor which calls ProcServ to boot an IOC

        Args:
            test_name: name of test we are running
            ioc: Dictionary containing
                device: String, Device name
                directory: String, the directory where st.cmd for the IOC is found
                var_dir: location of directory to write the log file
                port: The port to use
            test_mode: TestModes.RECSIM or TestModes.DEVSIM depending on IOC test mode
            var_dir: The directory into which the launcher will save log files.
        """
        super(ProcServLauncher, self).__init__(test_name, ioc, test_mode, var_dir)
        self.logport = int(self.macros["LOG_PORT"])

        self.procserv_port = get_free_ports(1)[0]

        self._telnet: telnetlib.Telnet | None = None
        self.autorestart = True
        self.original_macros = ioc.get("macros", {})

    def _get_telnet(self) -> telnetlib.Telnet:
        tn = self._telnet
        if tn is None:
            raise ValueError("Attempted to use telnet before it was set up")
        return tn

    def get_environment_vars(self) -> dict[str, str]:
        settings = super(ProcServLauncher, self).get_environment_vars()

        settings["CYGWIN"] = "disable_pcon"
        settings["MYDIRPROCSV"] = os.path.join(EPICS_TOP, "iocstartup")
        settings["EPICS_CAS_INTF_ADDR_LIST"] = "127.0.0.1"
        settings["EPICS_CAS_BEACON_ADDR_LIST"] = "127.255.255.255"
        settings["IOCLOGROOT"] = os.path.join("C:", "Instrument", "var", "logs", "ioc")
        settings["IOCCYGLOGROOT"] = self.to_cygwin_address(settings["IOCLOGROOT"])
        settings["IOCSH_SHOWWIN"] = "H"
        settings["LOGTIME"] = date.today().strftime("%Y%m%d")

        return settings

    @staticmethod
    def to_cygwin_address(win_filepath: str) -> str:
        """
        Converts a windows-style filepath to a / delimited path with cygdrive root
        Args:
            win_filepath: String, The filepath to be converted to a cygwin-style address

        Returns:
            cyg_address: String, the converted path

        """
        cyg_address = win_filepath.replace("C:\\", "/cygdrive/c/")
        cyg_address = cyg_address.replace("\\", "/")

        return cyg_address

    def _command_line(self) -> list[str]:
        comspec = os.getenv("ComSpec")
        cygwin_dir = self.to_cygwin_address(self._directory)
        return [
            "{}\\cygwin\\bin\\procServ.exe".format(self.ICPTOOLS),
            "--logstamp",
            '--logfile="{}"'.format(self.to_cygwin_address(self.log_file_name)),
            '--timefmt="%Y-%m-%d %H:%M:%S"',
            "--restrict",
            '--ignore="^D^C"',
            "--autorestart",
            "--wait",
            "--name={}".format(self._device.upper()),
            '--pidfile="/cygdrive/c/instrument/var/run/EPICS_{}.pid"'.format(self._device),
            "--logport={:d}".format(self.logport),
            '--chdir="{}"'.format(cygwin_dir),
            "{:d}".format(self.procserv_port),
            "{}".format(comspec),
            "/c",
            "runIOC.bat",
            "st.cmd",
        ]

    def open(self) -> None:
        """
        Overrides the open function to create a procserv telnet connection once IOC opened.

        Raises:
            OSError if procServ connection could not be made

        """
        super(ProcServLauncher, self).open()
        pids = ",".join([str(s) for s in self._find_processes()])
        print(
            f"IOC started, connecting to procserv pids {pids} at telnet port {self.procserv_port}"
        )

        timeout = 20

        self._telnet = telnetlib.Telnet("localhost", self.procserv_port, timeout=timeout)

        # Wait for procServ to become responsive by checking for the IOC started text
        init_output = (
            self._get_telnet()
            .read_until(self._ioc_started_text.encode("ascii"), timeout)
            .decode("ascii")
        )

        if "Welcome to procServ" not in init_output:
            raise OSError("Cannot connect to procServ over telnet")

    def send_telnet_command_and_retry_if_not_detected_condition_for_success(
        self, command: str, condition_for_success: Callable[[], bool], retry_limit: int
    ) -> None:
        """
        Send a command over telnet and detect if the condition for success has been met.
        Retry until the limit is reached and if the condition is not met raise an AssertionError.

        Args:
            command (str): The command to send over telnet
            condition_for_success (func): A function that returns True if condition met, and False
                if not
            retry_limit (int): The number of times you

        Raises:
            AssertionError: If the text has not been detected in the log after the given number of
                retries
        """
        for i in range(retry_limit):
            self.send_telnet_command(command)
            if condition_for_success():
                break
            else:
                self._get_telnet().close()
                self._get_telnet().open("localhost", self.procserv_port, timeout=20)
        else:  # If condition for success not detected, raise an assertion error
            raise AssertionError(
                "Sending telnet command {} failed {} times".format(command, retry_limit)
            )

    def send_telnet_command(self, command: str) -> None:
        """
        Send a command to the ioc via telnet. Command is sent and newline is appended
        Args:
            command: command to set
        """
        self._get_telnet().write("{cmd}\n".format(cmd=command).encode("ascii"))

    def force_manual_save(self) -> None:
        """
        Force a manual save by sending requests to save the settings and positions files
        """
        self.send_telnet_command("manual_save({}_info_settings.req)".format(self._device))
        self.send_telnet_command("manual_save({}_info_positions.req)".format(self._device))

    def start_ioc(self, wait: bool = False) -> None:
        """
        Start/restart IOC over telnet. (^X)

        Args:
            wait (bool): If this is true send the command and wait for the ioc started text to
                appear in the log, if the text doesn't appear retry (retries at most 3 times). If
                false just send the command and don't wait or retry.
        """
        start_command = "\x18"
        if wait:

            def condition_for_success() -> bool:
                try:
                    lfm = self.log_file_manager
                    assert lfm is not None
                    lfm.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START, self._ioc_started_text)
                except AssertionError:
                    return False
                else:
                    return True

            self.send_telnet_command_and_retry_if_not_detected_condition_for_success(
                start_command, condition_for_success, 3
            )
        else:
            self.send_telnet_command(start_command)

    def quit_ioc(self) -> None:
        """
        Sends the quit IOC command to procserv. (^Q)

        """
        quit_command = "\x11"
        self.send_telnet_command(quit_command)

    def toggle_autorestart(self) -> None:
        """
        Toggles whether the IOC is auto-restarts or not.

        """
        self._get_telnet().read_very_eager()

        autorestart_command = "-"
        self.send_telnet_command(autorestart_command)
        response = self._get_telnet().read_very_eager().decode("ascii")

        if "OFF" in response:
            self.autorestart = False
        elif "ON" in response:
            self.autorestart = True
        else:
            raise OSError("No response from procserv")

    def close(self) -> None:
        """
        Shuts telnet connection and kills IOC.
        Identifies the spawned procServ processes and kills them
        """
        print("\nTerminating IOC ({})".format(self._device))

        if self._telnet is not None:
            self._get_telnet().close()

        at_least_one_killed = False
        while True:
            pids = self._find_processes()
            if not pids:
                break

            at_least_one_killed = True

            for pid in pids:
                try:
                    os.kill(pid, SIGTERM)
                except ProcessLookupError:
                    # Process might have already been terminated
                    # we get two cygwin processes ids and killing one
                    # may have removed both processes
                    pass

            time.sleep(1)

        if not at_least_one_killed:
            print(
                "No process with name procServ.exe found that matched command line {}".format(
                    self.command_line
                )
            )

    def _find_processes(self) -> list[int]:
        pid_list = []
        for process in psutil.process_iter(attrs=["pid", "name"]):
            if process.info["name"] == "procServ.exe" and self.process_arguments_match_this_ioc(
                process.cmdline()
            ):
                # Command line arguments match
                pid_list.append(process.pid)
        return pid_list

    def process_arguments_match_this_ioc(self, process_arguments: list[str]) -> bool:
        """
        Compares the arguments this IOC was started with to the arguments of a process.
        Returns True if the arguments match

        Args:
            process_arguments: The command line arguments of the process to be considered

        Returns:
            arguments_match: Boolean: True if the process command line arguments match the IOC boot
                arguments, else False

        """
        # PSUtil strips quote marks (") from the command line used to spawn a process,
        # so we must remove them to compare with our ioc_run_command
        ioc_start_arguments = [args.replace('"', "") for args in self.command_line]

        arguments_match = all([args in process_arguments for args in ioc_start_arguments])

        return arguments_match

    @contextmanager
    def start_with_macros(
        self, macros: dict[str, str], pv_to_wait_for: str
    ) -> Generator[None, None, None]:
        """
        A context manager to start the ioc with the given macros and then at the end start
        the ioc again with the original macros.

        Args:
             macros (dict): A dictionary of macros to restart the ioc with.
             pv_to_wait_for (str): A pv to wait for 60 seconds to appear after starting the ioc.
        """
        ca = self.ca
        assert ca is not None
        try:
            self._start_with_macros(macros)
            ca.assert_that_pv_exists(pv_to_wait_for, timeout=60)
            yield
        finally:
            self._start_with_original_macros()
            ca.assert_that_pv_exists(pv_to_wait_for, timeout=60)

    def _start_with_macros(self, macros: dict[str, str], wait: bool = True) -> None:
        """
        Restart the ioc with the given macros

        Args
            macros (dict): A dictionary of macros to restart the ioc with.
        """
        self.macros = macros
        self.create_macros_file()
        time.sleep(1)
        self.start_ioc(wait)

    def _start_with_original_macros(self, wait: bool = True) -> None:
        """
        Restart the ioc with the macros originally set.
        """
        self.macros = self.original_macros
        self.create_macros_file()
        time.sleep(1)
        self.start_ioc(wait)


class IocLauncher(BaseLauncher):
    """
    Launches an IOC for testing.
    """

    def __init__(
        self, test_name: str, ioc: dict[str, Any], test_mode: TestModes, var_dir: str
    ) -> None:
        """
        Constructor that also launches the IOC.

        :param test_name: name of test we are running
        :param ioc: Dictionary containing:
            name: device name
            directory: the directory where the st.cmd for the IOC is found
            macros: the macros that should be passed to this IOC
            use_rec_sim: Use record simulation not device simulation in the ioc
            var_dir: location of directory to write log file and macros directories
            port: The port to use
        :param test_mode: TestModes.RECSIM or TestModes.DEVSIM depending on IOC test mode
        :param var_dir: The directory into which the launcher will save log files.
        """
        super(IocLauncher, self).__init__(test_name, ioc, test_mode, var_dir)

    def _command_line(self) -> list[str]:
        run_ioc_path = os.path.join(self._directory, "runIOC.bat")
        st_cmd_path = os.path.join(self._directory, "st.cmd")

        if not os.path.isfile(run_ioc_path):
            print("Run IOC path not found: '{0}'".format(run_ioc_path))
        if not os.path.isfile(st_cmd_path):
            print("St.cmd path not found: '{0}'".format(st_cmd_path))

        return [run_ioc_path, st_cmd_path]

    def close(self) -> None:
        """
        Closes the IOC.
        """
        print("\nTerminating IOC ({})".format(self._device))

        if self._process is not None:
            #  use write not communicate so that we don't wait for exit before continuing
            stdin = self._process.stdin
            assert stdin is not None
            stdin.write("exit\n".encode("utf-8"))
            stdin.flush()

            max_wait_for_ioc_to_die = 60
            wait_per_loop = 0.1

            for loop_count in range(int(max_wait_for_ioc_to_die / wait_per_loop)):
                try:
                    self._get_channel_access().assert_that_pv_does_not_exist(self._pv_for_existence)
                    break
                except AssertionError:
                    sleep(wait_per_loop)
                    if loop_count % 100 == 99:
                        print("   waited {}".format(loop_count * wait_per_loop))
            else:
                print(
                    "IOC process did not die after {} seconds after killing with `exit` in iocsh. "
                    "Killing process and waiting another {} seconds".format(
                        max_wait_for_ioc_to_die, max_wait_for_ioc_to_die
                    )
                )
                self._process.kill()
                sleep(max_wait_for_ioc_to_die)
                try:
                    self._get_channel_access().assert_that_pv_does_not_exist(self._pv_for_existence)
                    print("After killing process forcibly and waiting, IOC died correctly.")
                except AssertionError:
                    print(
                        "After killing process forcibly and waiting, IOC was still up. Will "
                        "continue anyway, but  the next set of tests to use this IOC are likely to "
                        "fail"
                    )

        self._print_log_file_location()

    def _print_log_file_location(self) -> None:
        if self.log_file_manager is not None:
            self.log_file_manager.close()
            print("IOC log written to {0}".format(self.log_file_name))


class PythonIOCLauncher(IocLauncher):
    """
    Launch a python ioc like REFL server.
    """

    def __init__(
        self, test_name: str, ioc: dict[str, Any], test_mode: TestModes, var_dir: str
    ) -> None:
        super(PythonIOCLauncher, self).__init__(test_name, ioc, test_mode, var_dir)
        self._python_script_commandline = ioc.get("python_script_commandline", None)

    def _command_line(self) -> list[str]:
        run_ioc_path = self._python_script_commandline[0]
        if not os.path.isfile(run_ioc_path):
            print("Command first argument path not found: '{0}'".format(run_ioc_path))
        command_line = [PYTHON3]
        command_line.extend(self._python_script_commandline)
        return command_line

    def close(self) -> None:
        """
        Closes the IOC.
        """
        print("\nTerminating python IOC ({})".format(self._device))

        if self._process is not None:
            # just kill a process if this is the only way to stop it
            self._process.kill()

        self._print_log_file_location()
