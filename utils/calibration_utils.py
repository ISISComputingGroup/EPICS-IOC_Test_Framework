from contextlib import contextmanager
import time

CAL_SEL_PV = "CAL:SEL"


def set_calibration_file(channel_access, filename, prefix=""):
    """
    Sets a calibration file. Retries if it didn't set properly first time.
    Args:
        channel_access: Channel Access object.
        filename: Calibration file name.
        prefix: Optional PV prefix in the format "PREFIX:".
    """
    max_retries = 10

    for _ in range(max_retries):
        channel_access.set_pv_value(f"{prefix}{CAL_SEL_PV}", filename)
        channel_access.assert_that_pv_alarm_is(f"{prefix}{CAL_SEL_PV}", channel_access.Alarms.NONE)
        time.sleep(3)
        channel_access.assert_that_pv_alarm_is(f"{prefix}{CAL_SEL_PV}:RBV", channel_access.Alarms.NONE)
        if channel_access.get_pv_value(f"{prefix}CAL:RBV") == filename:
            break
    else:
        raise Exception("Couldn't set calibration file to '{}' after {} tries".format(filename, max_retries))


def reset_calibration_file(channel_access, default_file="None.txt", prefix=""):
    set_calibration_file(channel_access, default_file, prefix)


@contextmanager
def use_calibration_file(channel_access, filename, default_file="None.txt", prefix=""):
    set_calibration_file(channel_access, filename, prefix)
    try:
        yield
    finally:
        reset_calibration_file(channel_access, default_file, prefix)
