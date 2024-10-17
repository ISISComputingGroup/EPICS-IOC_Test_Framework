import time
import typing
from contextlib import contextmanager

CAL_SEL_PV = "CAL:SEL"

if typing.TYPE_CHECKING:
    from utils.channel_access import ChannelAccess


def set_calibration_file(channel_access: "ChannelAccess", filename: str, prefix: str = "") -> None:
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
        channel_access.assert_that_pv_alarm_is(
            f"{prefix}{CAL_SEL_PV}:RBV", channel_access.Alarms.NONE
        )
        if channel_access.get_pv_value(f"{prefix}CAL:RBV") == filename:
            break
    else:
        raise Exception(
            "Couldn't set calibration file to '{}' after {} tries".format(filename, max_retries)
        )


def reset_calibration_file(
    channel_access: "ChannelAccess", default_file: str = "None.txt", prefix: str = ""
) -> None:
    set_calibration_file(channel_access, default_file, prefix)


@contextmanager
def use_calibration_file(
    channel_access: "ChannelAccess", filename: str, default_file: str = "None.txt", prefix: str = ""
) -> typing.Generator[None, None, None]:
    set_calibration_file(channel_access, filename, prefix)
    try:
        yield
    finally:
        reset_calibration_file(channel_access, default_file, prefix)
