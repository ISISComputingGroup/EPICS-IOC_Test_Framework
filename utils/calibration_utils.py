from contextlib import contextmanager
import time


def set_calibration_file(channel_access, filename):
    """
    Sets a calibration file. Retries if it didn't set properly first time.
    """
    max_retries = 10

    for _ in range(max_retries):
        channel_access.set_pv_value("CAL:SEL", filename)
        channel_access.assert_that_pv_alarm_is("CAL:SEL", channel_access.Alarms.NONE)
        time.sleep(3)
        channel_access.assert_that_pv_alarm_is("CAL:SEL:RBV", channel_access.Alarms.NONE)
        if channel_access.get_pv_value("CAL:RBV") == filename:
            break
    else:
        raise Exception("Couldn't set calibration file to '{}' after {} tries".format(filename, max_retries))


def reset_calibration_file(channel_access):
    set_calibration_file(channel_access, "None.txt")


@contextmanager
def use_calibration_file(channel_access, filename):
    set_calibration_file(channel_access, filename)
    try:
        yield
    finally:
        reset_calibration_file(channel_access)
