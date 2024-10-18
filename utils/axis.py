from utils.channel_access import ChannelAccess


def set_axis_moving(axis: str) -> None:
    ca_motors = ChannelAccess(device_prefix="MOT")
    current_position = ca_motors.get_pv_value(axis)
    low_limit = ca_motors.get_pv_value(axis + ":MTR.LLM")
    high_limit = ca_motors.get_pv_value(axis + ":MTR.HLM")
    assert isinstance(current_position, float)
    assert isinstance(low_limit, float)
    assert isinstance(high_limit, float)
    if current_position - low_limit < high_limit - current_position:
        ca_motors.set_pv_value(axis + ":SP", high_limit)
    else:
        ca_motors.set_pv_value(axis + ":SP", low_limit)


def stop_axis_moving(axis: str) -> None:
    ca_motors = ChannelAccess(device_prefix="MOT")
    ca_motors.set_pv_value(axis + ":MTR.STOP", 1, wait=True)


def assert_axis_moving(axis: str, timeout: int = 1) -> None:
    ca_motors = ChannelAccess(device_prefix="MOT")
    ca_motors.assert_that_pv_is(axis + ":MTR.MOVN", 1, timeout=timeout)


def assert_axis_not_moving(axis: str, timeout: int = 1) -> None:
    ca_motors = ChannelAccess(device_prefix="MOT")
    ca_motors.assert_that_pv_is(axis + ":MTR.MOVN", 0, timeout=timeout)
