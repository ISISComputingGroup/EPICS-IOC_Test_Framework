import subprocess
import os


class IocLauncher(object):
    """
    Launches an IOC for testing.
    """

    def __init__(self, directory):
        """
        Constructor that also launches the IOC.

        :param directory: the directory where the st.cmd for the IOC is found
        """
        print("Starting IOC")
        run_ioc_path = os.path.join(directory, 'runIOC.bat')
        st_cmd_path = os.path.join(directory, 'st.cmd')

        # As we need to use stdin to terminate the IOC, this means we also need to take care of stdout
        # So, we just dump it
        FNULL = open(os.devnull, 'w')
        self.proc = subprocess.Popen([run_ioc_path, st_cmd_path], creationflags=subprocess.CREATE_NEW_CONSOLE,
                                     cwd=directory, stdin=subprocess.PIPE, stdout=FNULL, stderr=subprocess.STDOUT)

    def close(self):
        """
        Closes the IOC.
        """
        print("Terminating IOC")
        # Need to send "exit" to the console as terminating the process won't work, because we ran a batch file
        self.proc.communicate("exit\n")

