import subprocess
import os

from utils.channel_access import ChannelAccess
from utils.log_file import log_filename


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

    def __init__(self, device, directory, use_rec_sim, var_dir):
        """
        Constructor that also launches the IOC.

        :param device: device name
        :param directory: the directory where the st.cmd for the IOC is found
        :param use_rec_sim: Use record simulation not device simulation in the ioc
        :param var_dir: location of directory to write log file and macros directories
        """
        self._directory = directory
        self.use_rec_sim = use_rec_sim
        self._process = None
        self._logFile = None
        self._device = device
        IOCRegister.uses_rec_sim = use_rec_sim
        self._ca = None
        self._var_dir = var_dir
        # port to use for the ioc
        self.port = None
        # macros to use for the ioc
        self.macros = None
        # prefix for the ioc
        self.device_prefix = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if self._logFile is not None:
            self._logFile.close()
            print("Lewis log written to {0}".format(self._log_filename()))

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

    def open(self):
        run_ioc_path = os.path.join(self._directory, 'runIOC.bat')
        st_cmd_path = os.path.join(self._directory, 'st.cmd')

        if not os.path.isfile(run_ioc_path):
            print("Run IOC path not found: '{0}'".format(run_ioc_path))
        if not os.path.isfile(st_cmd_path):
            print("St.cmd path not found: '{0}'".format(st_cmd_path))

        if self.device_prefix is not None:
            print("Check IOC is not running")
            ca = self._get_channel_access()
            try:
                ca.assert_pv_does_not_exist("DISABLE")
            except AssertionError as ex:
                raise AssertionError("IOC appears to already be running {0}".format(ex))

        ioc_run_commandline = [run_ioc_path, st_cmd_path]
        print("Starting IOC")

        settings = self._set_environment_vars()

        # create macros
        full_dir = os.path.join(self._var_dir, "tmp")
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)
        with open(os.path.join(full_dir, "test_config.txt"), mode="w") as f:
            for macro, value in self.macros.items():
                f.write("epicsEnvSet {macro} {value}\n".format(macro=macro, value=value))

        # To be able to see the IOC output for debugging, remove the redirection of stdin, stdout and stderr.
        # This does mean that the IOC will need to be closed manually after the tests.
        # Make sure to revert before checking code in
        self._logFile = open(self._log_filename(), "w")
        self._logFile.write("Started IOC with '{0}'".format(" ".join(ioc_run_commandline)))

        self._process = subprocess.Popen(ioc_run_commandline, creationflags=subprocess.CREATE_NEW_CONSOLE,
                                         cwd=self._directory, stdin=subprocess.PIPE, stdout=self._logFile,
                                         stderr=subprocess.STDOUT, env=settings)
										 

        if self.device_prefix is not None:
            ca = self._get_channel_access()
            try:
                ca.wait_for("DISABLE", timeout=30)
            except AssertionError as ex:
                raise AssertionError("IOC appears not to have started {0}".format(ex))

        IOCRegister.add_ioc(self._device, self)

    def close(self):
        """
        Closes the IOC.
        """
        if self._process is None:
            return
        print("Terminating IOC")
        # Need to send "exit" to the console as terminating the process won't work, because we ran a batch file
        self._process.communicate("exit\n")

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
            self._ca = ChannelAccess(device_prefix=self.device_prefix)

        return self._ca
