import os

# Directory for log files
LOG_FILES_DIRECTORY = os.path.join("logs","IOCTestFramework")


def log_filename(what, device, uses_rec_sim, var_dir):
    """
    Log file name with path. Ensure path exists
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
