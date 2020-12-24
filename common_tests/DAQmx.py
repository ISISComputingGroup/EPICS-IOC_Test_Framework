from time import sleep

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc, assert_log_messages


# Device prefix
DEVICE_PREFIX = "DAQMXTEST"
ICPCONFIGNAME = "DAQMX"


class DAQmxTests(object):
    """
    General tests for the DAQmx.
    """
    def setUp(self):
        self.emulator, self._ioc = get_running_lewis_and_ioc(DEVICE_PREFIX, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_emulator_disconnected_THEN_data_in_alarm_and_valid_on_reconnect(self):
        self.ca.assert_that_pv_alarm_is_not("DATA", ChannelAccess.Alarms.INVALID)
        self.emulator.disconnect_device()
        self.ca.assert_that_pv_alarm_is("DATA", ChannelAccess.Alarms.INVALID)

        # Check we don't get excessive numbers of messages if we stay disconnected for 15s (up to 15 messages seems
        # reasonable - 1 per second on average)
        with assert_log_messages(self._ioc, number_of_messages=15):
            sleep(15)
            # Double-check we are still in alarm
            self.ca.assert_that_pv_alarm_is("DATA", ChannelAccess.Alarms.INVALID)

        self.emulator.reconnect_device()
        self.ca.assert_that_pv_alarm_is_not("DATA", ChannelAccess.Alarms.INVALID, timeout=5)
        self.ca.assert_that_pv_value_is_changing("DATA", 1)


