import subprocess
import os

import time


class IocLauncher(object):
    """
    Launches an IOC for testing.
    """

    def __init__(self, directory, use_rec_sim, show_console):
        """
        Constructor that also launches the IOC.

        :param directory: the directory where the st.cmd for the IOC is found
        :param show_console: show the user a console.
        """
        self._directory = directory
        self._use_rec_sim = use_rec_sim
        self._show_console = show_console
        self.port = None
        self._proc = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        print("Starting IOC")
        run_ioc_path = os.path.join(self._directory, 'runIOC.bat')
        st_cmd_path = os.path.join(self._directory, 'st.cmd')

        settings = os.environ.copy()
        if self._use_rec_sim:
            # Using record simulation
            settings['TESTDEVSIM'] = '#'
            settings['TESTRECSIM'] = ' '
        else:
            # Not using record simulation
            settings['TESTDEVSIM'] = ' '
            settings['TESTRECSIM'] = '#'
        # Set the port
        settings['EMULATOR_PORT'] = str(self.port)

        # As we need to use stdin to terminate the IOC, this means we also need to take care of stdout
        # So, we just dump it
        FNULL = open(os.devnull, 'w')

        # To be able to see the IOC output for debugging, remove the redirection of stdin, stdout and stderr.
        # This does mean that the IOC will need to be closed manually after the tests.
        # Make sure to revert before checking code in
        if self._show_console:
            self._proc = subprocess.Popen([run_ioc_path, st_cmd_path], creationflags=subprocess.CREATE_NEW_CONSOLE,
                                          cwd=self._directory, env=settings)
        else:
            self._proc = subprocess.Popen([run_ioc_path, st_cmd_path], creationflags=subprocess.CREATE_NEW_CONSOLE,
                                          cwd=self._directory, stdin=subprocess.PIPE, stdout=FNULL,
                                          stderr=subprocess.STDOUT, env=settings)

    def close(self):
        """
        Closes the IOC.
        """
        if self._proc is None:
            return
        print("Terminating IOC")
        if self._show_console:
            self._proc.terminate()
        else:
            # Need to send "exit" to the console as terminating the process won't work, because we ran a batch file
            self._proc.communicate("exit\n")

    def wait_for_start(self):
        """
        Wait for IOC to start
        """

        print("Waiting for IOC to initialise")
        time.sleep(10)
