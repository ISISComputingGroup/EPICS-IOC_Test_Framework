import subprocess
import os
from time import sleep
from abc import ABCMeta

from utils.channel_access import ChannelAccess
from utils.log_file import log_filename, LogFileManager


EPICS_TOP = os.environ.get("KIT_ROOT", os.path.join("C:\\", "Instrument", "Apps", "EPICS"))
MAX_TIME_TO_WAIT_FOR_IOC_TO_START = 60


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
    __metaclass__ = ABCMeta

    def open(self):
        pass

    def close(self):
        pass

    def _set_environment_vars(self):
        pass


class ProcServLauncher(BaseLauncher):
    """
    Launches an IOC from procServ.exe
    """

    ICPTOOLS = "C:\\Instrument\\Apps\\EPICS\\tools\\master"

    def __init__(self, **kwargs):
        """
        Constructor which calls ProcServ to boot an IOC

        Args:
            device: String, Device name
            directory: String, the directory where st.cmd for the IOC is found
            var_dir: location of directory to write the log file
            port: The port to use
        """

        self._directory = kwargs['directory']
        self._device = kwargs['device']
        self._var_dir = kwargs['var_dir']
        self.port = kwargs['port']

        self.use_rec_sim = False

        self._process = None
        self.log_file_manager = None
        self._ca = None
        self.macros = None

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
        return settings

    def _log_filename(self):
        return log_filename("ioc", self._device, self.use_rec_sim, self._var_dir)

    def open(self):
        """
        Spawns the daemon IOC process using procServ.exe

        Returns:

        """

        st_cmd_path = os.path.join(self._directory, "st.cmd")

        if not os.path.isfile(st_cmd_path):
            print("St.cmd path not found: '{0}'".format(st_cmd_path))

        ca = self._get_channel_access()

        check_if_ioc_already_running(ca, self._device)

        ioc_run_command = ["{}\\cygwin_bin\\procServ.exe".format(self.ICPTOOLS),
                           '--logstamp', '--logfile', ' --timefmt="%%Y-%%m-%%d %%H:%%M:%%S"',
                           st_cmd_path, '--restrict', '--ignore=^D^C', '--noautorestart', '--wait',
                           '--name={}'.format(self._device),
                           '--pidfile="/cygdrive/c/windows/temp/EPICS_{}"'.format(self._device),
                           '--logport={:d}'.format(self.port + 1), '--chdir="{}"'.format(self._directory),
                           '{:d}'.format(self.port), '%ComSpec', '/c', 'runIOC.bat', 'st.cmd']

        print("Starting IOC ({})".format(self._device))

        settings = self._set_environment_vars()

        self.log_file_manager = LogFileManager(self._log_filename())
        self.log_file_manager.log_file.write("Started IOC with '{0}'".format(" ".join(ioc_run_command)))

        # To be able to see the IOC output for debugging, remove the redirection of stdin, stdout and stderr.
        # This does mean that the IOC will need to be closed manually after the tests.
        # Make sure to revert before checking code in
        self._process = subprocess.Popen(ioc_run_command, creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         cwd=self._directory,# stdin=subprocess.PIPE,
                                         stdout=self.log_file_manager.log_file, stderr=subprocess.STDOUT, env=settings)

        self.log_file_manager.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START)

        IOCRegister.add_ioc(self._device, self)

    def close(self):
        """
        Closes the IOC
        """
        if self._process is not None:
            self._process.kill()


class IocLauncher(BaseLauncher):
    """
    Launches an IOC for testing.
    """

    RECORD_THAT_ALWAYS_EXISTS = "DISABLE"

    def __init__(self, device, directory, macros, use_rec_sim, var_dir, port):
        """
        Constructor that also launches the IOC.

        :param device: device name
        :param directory: the directory where the st.cmd for the IOC is found
        :param macros: the macros that should be passed to this IOC
        :param use_rec_sim: Use record simulation not device simulation in the ioc
        :param var_dir: location of directory to write log file and macros directories
        :param port: The port to use
        """
        self._directory = directory
        self.use_rec_sim = use_rec_sim
        self._process = None
        self.log_file_manager = None
        self._device = device
        IOCRegister.uses_rec_sim = bool(use_rec_sim)
        self._ca = None
        self._var_dir = var_dir
        # port to use for the ioc
        self.port = port
        # macros to use for the ioc
        self.macros = macros

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
        return settings

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def open(self):
        run_ioc_path = os.path.join(self._directory, 'runIOC.bat')
        st_cmd_path = os.path.join(self._directory, 'st.cmd')

        if not os.path.isfile(run_ioc_path):
            print("Run IOC path not found: '{0}'".format(run_ioc_path))
        if not os.path.isfile(st_cmd_path):
            print("St.cmd path not found: '{0}'".format(st_cmd_path))

        ca = self._get_channel_access()
        try:
            print("Check that IOC is not running")
            ca.assert_that_pv_does_not_exist(self.RECORD_THAT_ALWAYS_EXISTS)
        except AssertionError as ex:
            raise AssertionError("IOC '{}' appears to already be running: {}".format(self._device, ex))

        ioc_run_commandline = [run_ioc_path, st_cmd_path]
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

        self.log_file_manager.wait_for_console(MAX_TIME_TO_WAIT_FOR_IOC_TO_START)

        IOCRegister.add_ioc(self._device, self)

    def close(self):
        """
        Closes the IOC.
        """
        print("Terminating IOC ({})".format(self._device))

        if self._process is not None:
            self._process.communicate("exit\n")

            max_wait_for_ioc_to_die = 60
            wait_per_loop = 0.1

            for _ in range(int(max_wait_for_ioc_to_die/wait_per_loop)):
                try:
                    self._get_channel_access().assert_that_pv_does_not_exist(self.RECORD_THAT_ALWAYS_EXISTS)
                    break
                except AssertionError:
                    sleep(wait_per_loop)
            else:
                print("IOC process did not die after {} seconds. Continuing anyway but next set of tests may fail."
                      .format(max_wait_for_ioc_to_die))

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
