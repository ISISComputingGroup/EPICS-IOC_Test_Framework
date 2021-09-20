import os
from time import sleep
import threading

# Directory for log files
LOG_FILES_DIRECTORY = os.path.join("logs", "IOCTestFramework")


def log_filename(test_name, what, device, uses_rec_sim, var_dir):
    """
    Log file name with path. Ensure path exists.

    :param test_name: name of test module being run
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

    return os.path.join(full_dir, "log_{test_name}_{sim_type}_{device}_{what}.log".format(
        test_name=test_name.replace('.','_'), sim_type=sim_type, device=device, what=what))


class LogFileManager(object):
    """
    Class to manage the access of log files
    """

    def __init__(self, filename):
        self.log_file = open(filename, "w+")

    def read_log(self):
        """
        Takes any new lines that have been written to the log and returns them

        Returns:
            new_messages (list): list of any new messages that have been received
        """
        new_messages = []
        while True:
            where = self.log_file.tell()
            mess = self.log_file.readline()
            if not mess:
                self.log_file.seek(where)
                break
            new_messages.append(mess)
            
        return new_messages

    def wait_for_console(self, timeout, ioc_started_text):
        """
        Waits until the ioc has started.

        Args:
            timeout (int): How long to wait before we assume the ioc has not started. (seconds)
            ioc_started_text (str): Text to look for in ioc log to indicate that the ioc has started
        """
        for i in range(timeout):
            new_messages = self.read_log()

            # uncomment for extra diagnostics
            # message_with_newline = [new_message.rstrip("\r\n") for new_message in new_messages]
            # print("    {}s: '{}'".format(i, "'\n       '".join(message_with_newline)))

            if any(ioc_started_text in line for line in new_messages):
                break

            sleep(1)
        else:
            raise AssertionError("IOC appears not to have started after {} seconds. Looking for '{}'"
                                 .format(timeout, ioc_started_text))

    def close(self):
        """
        Returns: close the log file
        """
        self.log_file.close()
