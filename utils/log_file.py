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


class LogFileWriter(object):
    lines = list()
    reading = True
    writing_lock = threading.RLock()
    ioc_started = False

    def __init__(self, filename, log_pipe):
        self.filename = filename
        self.log_pipe = log_pipe
        self.read_thread = threading.Thread(target=self.consume_pipe)
        self.read_thread.setDaemon(True)
        self.read_thread.start()

    def write(self, message):
        """
        Appends a message to the log.

        Args:
            message (str): The message to append
        """
        with self.writing_lock:
            self.lines.append(message)

    def consume_pipe(self):
        """
        Takes any files that have been written to the pipe and puts them in the buffer.
        """
        while self.reading:
            message = self.log_pipe.readline()

            # Look for epics> in the IOC log which means that the IOC has successfully started.
            self.ioc_started = "epics>" in message

            self.write(message)

    def wait_for_console(self, timeout):
        """
        Waits until the ioc has started.

        Args:
            timeout (int): How long to wait before we assume the ioc has not started. (seconds)
        """
        for i in range(timeout):
            if self.ioc_started:
                break
            sleep(1)
        else:
            self.flush_to_file()
            raise AssertionError("IOC appears not to have started after {} seconds."
                                 .format(timeout))

    def flush_to_file(self):
        """
        Writes the log buffer to file and clears the buffer.
        """
        with open(self.filename, "w") as f:
            f.writelines(self.lines)
        with self.writing_lock:
            self.lines = list()

    def stop_logging(self, timeout=0.5):
        """
        Stops reading the log pipe.

        Args:
            timeout (float): The time to wait for the reading thread to join (in seconds)
        """
        self.reading = False
        self.log_pipe.close()
        self.read_thread.join(timeout)
