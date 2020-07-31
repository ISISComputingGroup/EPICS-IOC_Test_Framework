from utils.channel_access import ChannelAccess


def set_axis_moving(axis):
    ca_motors = ChannelAccess(device_prefix="MOT")
    current_position = ca_motors.get_pv_value(axis)
    low_limit = ca_motors.get_pv_value(axis + ":MTR.LLM")
    high_limit = ca_motors.get_pv_value(axis + ":MTR.HLM")
    if current_position - low_limit < high_limit - current_position:
        ca_motors.set_pv_value(axis + ":SP", high_limit)
    else:
        ca_motors.set_pv_value(axis + ":SP", low_limit)


def assert_axis_moving(axis, retry_count=1):
    ca_motors = ChannelAccess(device_prefix="MOT")
    for i in range(retry_count):
        try:
            ca_motors.assert_that_pv_is(axis + ":MTR.MOVN", 1)
            break
        except AssertionError:
            continue
    else:
        raise AssertionError("Axis {}:MTR.MOVN is 0 i.e. not moving. Retry count was {} times".format(axis, retry_count))


def assert_axis_not_moving(axis, retry_count=1):
    ca_motors = ChannelAccess(device_prefix="MOT")
    for i in range(retry_count):
        try:
            ca_motors.assert_that_pv_is(axis + ":MTR.MOVN", 0)
            break
        except AssertionError:
            continue
    else:
        raise AssertionError("Axis {}:MTR.MOVN is 1 i.e. moving. Retry count was {} times".format(axis, retry_count))
