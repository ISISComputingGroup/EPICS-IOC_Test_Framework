import os
from time import sleep
import threading

# Directory for log files
LOG_FILES_DIRECTORY = os.path.join("logs","IOCTestFramework")


def log_filename(what, device, uses_rec_sim, var_dir):
    """
    Log file name with path. Ensure path exists.

    :param what: what is being logged for, e.g. lewis
    :param device: device the log is for
    :param uses_rec_sim: whether rec sim is used
    :param var_dir: location of directory to write log file
    :return: path
    """
    if uses_rec_sim:
        sim_type = "recsim"
    else:
        sim_type = "devsim"
    full_dir = os.path.join(var_dir, LOG_FILES_DIRECTORY)
    if not os.path.exists(full_dir):
        os.makedirs(full_dir)

    return os.path.join(full_dir, "log_{device}_{sim_type}_{what}.log".format(
        device=device, what=what, sim_type=sim_type))


class LogFileManager(object):
    reading_from = 0

    def __init__(self, filename):
        self.log_file = open(filename, "w+")

    def read_log(self):
        """
        Takes any new lines that have been written to the log and returns them

        Returns:
            new_messages (list): list of any new messages that have been received
        """
        self.log_file.seek(self.reading_from)
        new_messages = list(self.log_file)
        self.reading_from = self.log_file.tell()
        return new_messages

    def wait_for_console(self, timeout):
        """
        Waits until the ioc has started.

        Args:
            timeout (int): How long to wait before we assume the ioc has not started. (seconds)
        """
        for i in range(timeout):
            new_messages = self.read_log()

            if any("epics>" in line for line in new_messages):
                break

            sleep(1)
        else:
            raise AssertionError("IOC appears not to have started after {} seconds."
                                 .format(timeout))

    def close(self):
        self.log_file.close()
