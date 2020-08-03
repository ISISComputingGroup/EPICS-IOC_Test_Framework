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


def assert_axis_moving(axis):
    ca_motors = ChannelAccess(device_prefix="MOT")
    ca_motors.assert_that_pv_is(axis + ":MTR.MOVN", 1, timeout=1)


def assert_axis_not_moving(axis):
    ca_motors = ChannelAccess(device_prefix="MOT")
    ca_motors.assert_that_pv_is(axis + ":MTR.MOVN", 0, timeout=1)
