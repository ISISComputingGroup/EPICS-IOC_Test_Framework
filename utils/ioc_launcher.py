import subprocess
import os
from time import sleep

from utils.channel_access import ChannelAccess
from utils.log_file import log_filename


EPICS_TOP = os.path.join("C:\\", "Instrument", "Apps", "EPICS")
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


class IocLauncher(object):
    """
    Launches an IOC for testing.
    """

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
        self._logFile = None
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
            pv = "{}:DISABLE".format(self._device)
            print("Check that IOC is not running".format(pv))
            ca.assert_pv_does_not_exist(pv)
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

        # To be able to see the IOC output for debugging, remove the redirection of stdin, stdout and stderr.
        # This does mean that the IOC will need to be closed manually after the tests.
        # Make sure to revert before checking code in
        self._logFile = open(self._log_filename(), "w")
        self._logFile.write("Started IOC with '{0}'".format(" ".join(ioc_run_commandline)))

        self._process = subprocess.Popen(ioc_run_commandline, creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         cwd=self._directory, stdin=subprocess.PIPE, stdout=self._logFile,
                                         stderr=subprocess.STDOUT, env=settings)

        # Look for epics> in the IOC log which means that the IOC has successfully started.
        for i in range(MAX_TIME_TO_WAIT_FOR_IOC_TO_START):
            with open(self._log_filename()) as f:
                if any("epics>" in line for line in f.readlines()):
                    break
            sleep(1)
        else:
            raise AssertionError("IOC appears not to have started after {} seconds."
                                 .format(MAX_TIME_TO_WAIT_FOR_IOC_TO_START))

        IOCRegister.add_ioc(self._device, self)

    def close(self):
        """
        Closes the IOC.
        """
        print("Terminating IOC ({})".format(self._device))

        if self._process is not None:
            # Need to send "exit" to the console as terminating the process won't work, because we ran a batch file
            self._process.communicate("exit\n")

        if self._logFile is not None:
            self._logFile.close()
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
            self._ca = ChannelAccess()

        return self._ca
