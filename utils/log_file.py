import os
from time import sleep

from utils.test_modes import TestModes

# Directory for log files
LOG_FILES_DIRECTORY = os.path.join("logs", "IOCTestFramework")


def log_filename(test_name, what, device, test_mode, var_dir):
    """
    Log file name with path. Ensure path exists.

    :param test_name: name of test module being run
    :param what: what is being logged for, e.g. lewis
    :param device: device the log is for
    :param test_mode: testing mode
    :param var_dir: location of directory to write log file
    :return: path
    """
    if test_mode == TestModes.RECSIM:
        sim_type = "recsim"
    elif test_mode == TestModes.DEVSIM:
        sim_type = "devsim"
    else:
        sim_type = "nosim"
    full_dir = os.path.join(var_dir, LOG_FILES_DIRECTORY)
    if not os.path.exists(full_dir):
        os.makedirs(full_dir)

    return os.path.join(
        full_dir,
        "log_{test_name}_{sim_type}_{device}_{what}.log".format(
            test_name=test_name.replace(".", "_"), sim_type=sim_type, device=device, what=what
        ),
    )


class LogFileManager(object):
    """
    Class to manage the access of log files
    """

    def __init__(self, filename):
        self.log_file_w = open(filename, "w", 1)
        self.log_file_r = open(filename, "r")

    def read_log(self):
        """
        Takes any new lines that have been written to the log and returns them

        Returns:
            new_messages (list): list of any new messages that have been received
        """
        new_messages = []
        while True:
            where = self.log_file_r.tell()
            mess = self.log_file_r.readline()
            if not mess:
                self.log_file_r.seek(where)
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
            raise AssertionError(
                "IOC appears not to have started after {} seconds. Looking for '{}'".format(
                    timeout, ioc_started_text
                )
            )

    def close(self):
        """
        Returns: close the log file
        """
        self.log_file_r.close()
        self.log_file_w.close()
