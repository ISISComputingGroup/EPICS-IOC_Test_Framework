import subprocess


class LewisLauncher(object):
    """
    Launches Lewis.
    """

    def __init__(self, cmd):
        """
        Constructor that also launches Lewis.

        :param cmd: the cmd string for configuring Lewis
        """
        print("Starting Lewis")
        self.proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def close(self):
        """
        Closes the Lewis session by killing the process.
        """
        print("Terminating Lewis")
        self.proc.terminate()
