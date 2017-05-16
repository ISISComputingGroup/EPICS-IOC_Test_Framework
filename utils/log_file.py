import os

# Directory for log files
LOG_FILES_DIRECTORY = "log"


def log_filename(what, device, uses_rec_sim):
    """
    Log file name with path. Ensure path exists
    :param what: what is being logged for, e.g. lewis
    :param device: device the log is for
    :param uses_rec_sim: whether rec sim is used
    :return: path
    """
    if uses_rec_sim:
        sim_type = "recsim"
    else:
        sim_type = "devsim"
    if not os.path.exists(LOG_FILES_DIRECTORY):
        os.mkdir(LOG_FILES_DIRECTORY)
    return os.path.join(LOG_FILES_DIRECTORY, "log_{device}_{sim_type}_{what}.log".format(
        device=device, what=what, sim_type=sim_type))
