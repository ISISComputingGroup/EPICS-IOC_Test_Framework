"""
Code that launches an IOC/application under test
"""
import subprocess
import os
import psutil
from time import sleep
from abc import ABCMeta

from utils.channel_access import ChannelAccess
from utils.log_file import log_filename, LogFileManager
from utils.test_modes import TestModes
from datetime import date
import telnetlib
from signal import SIGTERM
import atexit

APPS_BASE = os.path.join("C:\\", "Instrument", "Apps")
EPICS_TOP = os.environ.get("KIT_ROOT", os.path.join(APPS_BASE, "EPICS"))
PYTHON = os.environ.get("PYTHON", os.path.join(APPS_BASE, "Python", "python.exe"))

MAX_TIME_TO_WAIT_FOR_IOC_TO_START = 120

EPICS_CASE_ENVIRONMENT_VARS = {
    "EPICS_CAS_INTF_ADDR_LIST": "127.0.0.1",
    "EPICS_CAS_BEACON_ADDR_LIST": "127.255.255.255"}


def get_default_ioc_dir(iocname, iocnum=1):
    """
    Gets the default path to run the IOC given the name.
    Args:
        iocname: the name of the ioc
        iocnum: the number of the ioc to start (defaults to 1)
    Returns:
        the path
    """
    return os.path.join(EPICS_TOP, "ioc", "master", iocname, "iocBoot", "ioc{}-IOC-{:02d}".format(iocname, iocnum))


def check_if_ioc_already_running(ca, device, test_pv="DISABLE"):
    """
    Checks to see if a IOC is already running by asserting that a pv does not exist.
    Args:
        ca: channel access
        device: the device
        test_pv: the name of the test pv

    Returns:

    """
    try:
        print("Check that IOC is not running")
        ca.assert_that_pv_does_not_exist(test_pv)
    except AssertionError as ex:
        raise AssertionError("IOC '{}' appears to already be running: {}".format(device, ex))


class IOCRegister(object):
    """
    A way of registering running iocs.
    """

    # Static dictionary of running iocs
    RunningIOCs = {}

    uses_rec_sim = False

    @classmethod
    def get_running(cls, ioc_name):
        """
        Get a running ioc by name, return None if not running.

        :param ioc_name: name of the ioc emulator to grab
        :return: ioc launcher
        """
        return cls.RunningIOCs.get(ioc_name)

    @classmethod
    def add_ioc(cls, name, ioc):
        """
        Add an ioc to the running list.

        :param name: name of the ioc
        :param ioc: the ioc launcher
        :return:
        """
        cls.RunningIOCs[name] = ioc


class BaseLauncher(object):
    """
    Launcher base, this is the base class for a launcher of application under test.
    """
    __metaclass__ = ABCMeta

    def open(self):
        """
        Starts the application under test.
        """
        pass

    def close(self):
        """
        Exits the application under test
        """
        pass

    def _set_environment_vars(self):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()


class ProcServLauncher(BaseLauncher):
    """
    Launches an IOC from procServ.exe
    """

    ICPTOOLS = os.path.join(EPICS_TOP, "tools", "master")

    def __init__(self, ioc, test_mode, var_dir):
        """
        Constructor which calls ProcServ to boot an IOC

        Args:
            ioc: Dictionary containing
                device: String, Device name
                directory: String, the directory where st.cmd for the IOC is found
                var_dir: location of directory to write the log file
                port: The port to use
            test_mode: Ignored by non-emulator launchers
            var_dir: The directory into which the launcher will save log files.
        """

        self._directory = ioc['directory']
        self._device = ioc['name']
        self._var_dir = var_dir
        self.port = int(ioc['macros']['EMULATOR_PORT'])
        self.logport = int(ioc['macros']['LOG_PORT'])
        self._ioc_started_text = ioc.get("started_text", "epics>")

        self.ioc_run_command = None
        self._process = None
        self.log_file_manager = None
        self._ca = None
        self.macros = None
        self.telnet = None
        self.autorestart = True

        atexit.register(self.close)

    def _get_channel_access(self):
        """
        :return (ChannelAccess): the channel access component
        """
        if self._ca is None:
            self._ca = ChannelAccess(device_prefix=self._device)

        return self._ca

    def _set_environment_vars(self):
        settings = os.environ.copy()

        # Set the port
        settings['EMULATOR_PORT'] = str(self.port)

        settings["CYGWIN"] = "nodosfilewarning"
        settings["MYDIRPROCSV"] = os.path.join(EPICS_TOP, "iocstartup")
        settings["EPICS_CAS_INTF_ADDR_LIST"] = "127.0.0.1"
        settings["EPICS_CAS_BEACON_ADDR_LIST"] = "127.255.255.255"
        settings["IOCLOGROOT"] = os.path.join("C:", "Instrument", "var", "logs", "ioc")
        settings["IOCCYGLOGROOT"] = self.to_cygwin_address(settings["IOCLOGROOT"])
        settings["IOCSH_SHOWWIN"] = "H"
        settings["LOGTIME"] = date.today().strftime("%Y%m%d")

        return settings

    def _log_filename(self):
        return log_filename("ioc", self._device, True, self._var_dir)

    @staticmethod
    def to_cygwin_address(win_filepath):
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

    def open(self):
        """
        Spawns the daemon IOC process using procServ.exe. Call signature found in iocstartup/procserv.bat

        Returns:

        """
        st_cmd_path = os.path.join(self._directory, "st.cmd")

        if not os.path.isfile(st_cmd_path):
            print("St.cmd path not found: '{0}'".format(st_cmd_path))

        ca = self._get_channel_access()

        check_if_ioc_already_running(ca, self._device)

        comspec = os.getenv("ComSpec")

        cygwin_dir = self.to_cygwin_address(self._directory)
        self.ioc_run_command = ["{}\\cygwin_bin\\procServ.exe".format(self.ICPTOOLS), '--logstamp',
                                '--logfile="{}"'.format(self.to_cygwin_address(self._log_filename())),
                                '--timefmt="%Y-%m-%d %H:%M:%S"',
                                '--restrict', '--ignore="^D^C"', '--autorestart', '--wait',
                                '--name={}'.format(self._device.upper()),
                                '--pidfile="/cygdrive/c/windows/temp/EPICS_{}.pid"'.format(self._device),
                                '--logport={:d}'.format(self.logport), '--chdir="{}"'.format(cygwin_dir),
                                '{:d}'.format(self.port), '{}'.format(comspec), '/c', 'runIOC.bat', 'st.cmd']

        print("Starting IOC ({})".format(self._device))

        settings = self._set_environment_vars()

        self.log_file_manager = LogFileManager(self._log_filename())
        self.log_file_manager.log_file.write("Started IOC with '{0}'\n".format(" ".join(self.ioc_run_command)))

        # To be able to see the IOC output for debugging, remove the redirection of stdin, stdout and stderr.
        # This does mean that the IOC will need to be closed manually after the tests.
        # Make sure to revert before checking code in

        self._process = subprocess.Popen(' '.join(self.ioc_run_command), creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         cwd=self._directory, stdout=self.log_file_manager.log_file,
                                         stderr=subprocess.STDOUT, env=settings)

        self.connect_to_procserv()
        self.start_ioc()

        self.log_file_manager.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START, self._ioc_started_text)

        IOCRegister.add_ioc(self._device, self)

    def connect_to_procserv(self):
        """
        Opens the telnet connection to the procserv daemon.

        """
        self.telnet = telnetlib.Telnet("localhost", self.port, timeout=10)

        # Wait for procServ to become responsive
        sleep(5)
        init_output = self.telnet.read_very_eager()

        if "Welcome to procServ" not in init_output:
            raise OSError("Cannot connect to procServ over telnet")

    def start_ioc(self):
        """
        Sends the start/restart IOC command to procserv. (^X)

        """
        start_command = "\x18"
        self.telnet.write(start_command + "\n")

    def quit_ioc(self):
        """
        Sends the quit IOC command to procserv. (^Q)

        """
        quit_command = "\x11"
        self.telnet.write(quit_command + "\n")

    def toggle_autorestart(self):
        """
        Toggles whether the IOC is auto-restarts or not.

        """
        self.telnet.read_very_eager()

        autorestart_command = "-"
        self.telnet.write(autorestart_command + "\n")
        response = self.telnet.read_very_eager()

        if "OFF" in response:
            self.autorestart = False
        elif "ON" in response:
            self.autorestart = True
        else:
            raise OSError("No response from procserv")

    def close(self):
        """
        Shuts telnet connection and kills IOC. Identifies the spawned procServ processes and kills them

        """

        if self.telnet is not None:
            self.telnet.close()

        # PSUtil strips quote marks (") from the command line used to spawn a process,
        # so we must remove them to compare with our ioc_run_command
        cmdline_arguments = [args.replace('"', '') for args in self.ioc_run_command]

        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'procServ.exe':
                if all([args in process.cmdline() for args in cmdline_arguments]):
                    # Command line arguments match, kill procServ instance
                    os.kill(process.pid, SIGTERM)


class IocLauncher(BaseLauncher):
    """
    Launches an IOC for testing.
    """
    def __init__(self, ioc, test_mode, var_dir):
        """
        Constructor that also launches the IOC.

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
        self._device = ioc['name']
        self._directory = ioc['directory']
        self.macros = ioc.get("macros", {})
        self._var_dir = var_dir
        self.port = self.macros['EMULATOR_PORT']
        self._ioc_started_text = ioc.get("started_text", "epics>")
        self._pv_for_existence = ioc.get("pv_for_existence", "DISABLE")
        self._extra_environment_vars = ioc.get("environment_vars", {})

        if test_mode not in [TestModes.RECSIM, TestModes.DEVSIM]:
            raise ValueError("Invalid test mode provided")

        self.use_rec_sim = test_mode == TestModes.RECSIM

        IOCRegister.uses_rec_sim = self.use_rec_sim
        self._ca = None
        self._process = None
        self.log_file_manager = None

    def _log_filename(self):
        return log_filename("ioc", self._device, self.use_rec_sim, self._var_dir)

    def _set_environment_vars(self):
        settings = os.environ.copy()
        if self.use_rec_sim:
            # Using record simulation
            settings['TESTDEVSIM'] = ''
            settings['TESTRECSIM'] = 'yes'
        else:
            # Not using record simulation
            settings['TESTDEVSIM'] = 'yes'
            settings['TESTRECSIM'] = ''

        # Set the port
        settings['EMULATOR_PORT'] = str(self.port)

        for env_name, setting in self._extra_environment_vars.items():
            settings[env_name] = setting
        return settings

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def _command_line(self):
        run_ioc_path = os.path.join(self._directory, 'runIOC.bat')
        st_cmd_path = os.path.join(self._directory, 'st.cmd')

        if not os.path.isfile(run_ioc_path):
            print("Run IOC path not found: '{0}'".format(run_ioc_path))
        if not os.path.isfile(st_cmd_path):
            print("St.cmd path not found: '{0}'".format(st_cmd_path))

        return [run_ioc_path, st_cmd_path]

    def open(self):
        """
        Runs the ioc.
        """
        ioc_run_commandline = self._command_line()

        ca = self._get_channel_access()
        try:
            print("Check that IOC is not running")
            ca.assert_that_pv_does_not_exist(self._pv_for_existence)
        except AssertionError as ex:
            raise AssertionError("IOC '{}' appears to already be running: {}".format(self._device, ex))

        print("Starting IOC ({})".format(self._device))

        settings = self._set_environment_vars()

        # create macros
        full_dir = os.path.join(self._var_dir, "tmp")
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)
        with open(os.path.join(full_dir, "test_config.txt"), mode="w") as f:
            for macro, value in self.macros.items():
                f.write('epicsEnvSet("{macro}", "{value}")\n'
                        .format(macro=macro.replace('"', '\\"'), value=str(value).replace('"', '\\"')))

        self.log_file_manager = LogFileManager(self._log_filename())
        self.log_file_manager.log_file.write("Started IOC with '{0}'".format(" ".join(ioc_run_commandline)))

        # To be able to see the IOC output for debugging, remove the redirection of stdin, stdout and stderr.
        # This does mean that the IOC will need to be closed manually after the tests.
        # Make sure to revert before checking code in
        self._process = subprocess.Popen(ioc_run_commandline, creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         cwd=self._directory, stdin=subprocess.PIPE,
                                         stdout=self.log_file_manager.log_file, stderr=subprocess.STDOUT, env=settings)

        # Write a return so that an epics terminal will appear after boot
        self._process.stdin.write("\n")
        self.log_file_manager.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START, self._ioc_started_text)

        IOCRegister.add_ioc(self._device, self)

    def close(self):
        """
        Closes the IOC.
        """
        print("Terminating IOC ({})".format(self._device))

        if self._process is not None:
            #  use write not communicate so that we don't wait for exit before continuing
            self._process.stdin.write("exit\n")

            max_wait_for_ioc_to_die = 60
            wait_per_loop = 0.1

            for loop_count in range(int(max_wait_for_ioc_to_die/wait_per_loop)):
                try:
                    self._get_channel_access().assert_that_pv_does_not_exist(self._pv_for_existence)
                    break
                except AssertionError:
                    sleep(wait_per_loop)
                    if loop_count % 100 == 99:
                        print("   waited {}".format(loop_count*wait_per_loop))
            else:
                print("IOC process did not die after {} seconds. Continuing anyway but next set of tests may fail."
                      .format(max_wait_for_ioc_to_die))
                self._process.kill()

        self._print_log_file_location()

    def _print_log_file_location(self):
        if self.log_file_manager is not None:
            self.log_file_manager.close()
            print("IOC log written to {0}".format(self._log_filename()))

    def set_simulated_value(self, pv_name, value):
        """
        If this IOC is in rec sim set the PV value.

        :param pv_name: name of the pv value
        :param value: value to set
        :return:
        """

        if self.use_rec_sim:
            ca = self._get_channel_access()
            ca.set_pv_value(pv_name, value)

    def _get_channel_access(self):
        """
        :return (ChannelAccess): the channel access component
        """
        if self._ca is None:
            self._ca = ChannelAccess(device_prefix=self._device)

        return self._ca


class PythonIOCLauncher(IocLauncher):
    """
    Launch a python ioc like REFL server.
    """

    def __init__(self, ioc, test_mode, var_dir):
        super(PythonIOCLauncher, self).__init__(ioc, test_mode, var_dir)
        self._python_script_commandline = ioc.get("python_script_commandline", None)

    def _command_line(self):
        run_ioc_path = self._python_script_commandline[0]
        if not os.path.isfile(run_ioc_path):
            print("Command first argument path not found: '{0}'".format(run_ioc_path))
        command_line = [PYTHON]
        command_line.extend(self._python_script_commandline)
        return command_line

    def _set_environment_vars(self):
        settings = super(PythonIOCLauncher, self)._set_environment_vars()
        settings["PYTHONUNBUFFERED"] = "TRUE"
        settings.update(EPICS_CASE_ENVIRONMENT_VARS)

        return settings

    def close(self):
        """
        Closes the IOC.
        """
        print("Terminating python IOC ({})".format(self._device))

        if self._process is not None:
            # just kill a process if this is the only way to stop it
            self._process.kill()

        self._print_log_file_location()
