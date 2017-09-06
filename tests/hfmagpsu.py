import unittest
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from datetime import datetime, date, timedelta


class HfmagpsuTests(unittest.TestCase):


    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("HFMAGPSU") # emulator name
        self.ca = ChannelAccess(default_timeout=10)
        self.ca.wait_for("HFMAGPSU_01:DIRECTION", timeout=10)

    def _write_direction(self, direction):
        self.ca.set_pv_value("HFMAGPSU_01:DIRECTION:SP", direction)

    def _write_output_mode(self, new_output_mode):
        self.ca.set_pv_value("HFMAGPSU_01:OUTPUTMODE:SP", new_output_mode)

    def _write_ramp_target(self, new_ramp_target):
        self.ca.set_pv_value("HFMAGPSU_01:RAMPTARGET:SP", new_ramp_target)

    def _write_heater_status(self, new_heater_status):
        self.ca.set_pv_value("HFMAGPSU_01:HEATERSTATUS:SP", new_heater_status)

    def _write_heater_value(self, new_heater_value):
        self.ca.set_pv_value("HFMAGPSU_01:HEATERVALUE:SP", new_heater_value)

    def _write_max_target(self, new_max):
        self.ca.set_pv_value("HFMAGPSU_01:MAX:SP", new_max)

    def _write_mid_target(self, new_mid):
        self.ca.set_pv_value("HFMAGPSU_01:MID:SP", new_mid)

    def _write_ramp_rate(self, new_rate):
        self.ca.set_pv_value("HFMAGPSU_01:RAMPRATE:SP", new_rate)

    def _write_pause(self, new_pause):
        self.ca.set_pv_value("HFMAGPSU_01:PAUSE:SP", new_pause)

    def _write_limit(self, new_limit):
        self.ca.set_pv_value("HFMAGPSU_01:LIMIT:SP", new_limit)

    ''' Retrieve time from the log message PV and parse to a datetime object '''
    def get_log_message_time(self, log_message):
        time_string = log_message[:8]
        time_object = datetime.strptime(time_string, '%H:%M:%S')
        return time_object

    def test_GIVEN_midTarget_set_WHEN_read_THEN_midTarget_is_as_expected(self):
        expected_mid_target = 2.0
        self._write_mid_target(expected_mid_target)
        self.ca.assert_that_pv_is("HFMAGPSU_01:MID", expected_mid_target)

    def test_GIVEN_rampRate_set_WHEN_read_THEN_rampRate_is_as_expected(self):
        expected_ramp_rate = 0.25
        self._write_ramp_rate(expected_ramp_rate)
        self.ca.assert_that_pv_is("HFMAGPSU_01:RAMPRATE", expected_ramp_rate)

    def test_GIVEN_maxTarget_set_WHEN_read_THEN_maxTarget_is_as_expected(self):
        expected_max_target = 4.0
        self._write_max_target(expected_max_target)
        self.ca.assert_that_pv_is("HFMAGPSU_01:MAX", expected_max_target)

    def test_GIVEN_limit_set_WHEN_read_THEN_limit_is_as_expected(self):
        expected_output = 35.5
        self._write_limit(expected_output)
        self.ca.assert_that_pv_is("HFMAGPSU_01:LIMIT", expected_output)

    def test_GIVEN_heaterValue_set_WHEN_read_THEN_heaterValue_is_as_expected(self):
        expected_heater_value = 15.5
        self._write_heater_value(expected_heater_value)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERVALUE", expected_heater_value)

    def test_GIVEN_pause_set_ON_WHEN_read_THEN_pause_is_as_expected(self):
        expected_output = 'ON'
        self._write_pause(True)
        self.ca.assert_that_pv_is("HFMAGPSU_01:PAUSE", expected_output)

    def test_GIVEN_pause_set_OFF_WHEN_read_THEN_pause_is_as_expected(self):
        expected_output = 'OFF'
        self._write_pause(False)
        self.ca.assert_that_pv_is("HFMAGPSU_01:PAUSE", expected_output)

    def test_GIVEN_outputMode_set_TESLA_WHEN_read_THEN_outputMode_is_as_expected(self):
        expected_mode_str = 'TESLA'
        self._write_output_mode(True)
        self.ca.assert_that_pv_is("HFMAGPSU_01:OUTPUTMODE", expected_mode_str)

    def test_GIVEN_outputMode_set_AMPS_WHEN_read_THEN_outputMode_is_as_expected(self):
        expected_mode_str = 'AMPS'
        self._write_output_mode(False)
        self.ca.assert_that_pv_is("HFMAGPSU_01:OUTPUTMODE", expected_mode_str)

    def test_GIVEN_heaterStatus_set_ON_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_heaterStatus = 'ON'
        self._write_heater_status(True)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERSTATUS", expected_heaterStatus)

    def test_GIVEN_heaterStatus_set_OFF_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_heaterStatus = 'OFF'
        self._write_heater_status(False)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERSTATUS", expected_heaterStatus)

    def test_GIVEN_rampTarget_set_WHEN_read_THEN_rampTarget_is_as_expected(self):
        ramp_targets = ['ZERO', 'MID', 'MAX']
        for index, value in enumerate(ramp_targets):
            self._write_ramp_target(index)
            expected_target = value
            self.ca.assert_that_pv_is("HFMAGPSU_01:RAMPTARGET", expected_target)

    def test_GIVEN_direction_set_WHEN_read_THEN_direction_is_as_expected(self):
        directions = ['-', '0', '+']
        for index, value in enumerate(directions):
            self._write_direction(index)
            expected_direction = value
            self.ca.assert_that_pv_is("HFMAGPSU_01:DIRECTION", expected_direction)

    """
    As the log message contains a timestamp and the setpoint/test timestamps will differ
    by a few seconds, we're testing to see if the timestamp difference is within 3 seconds.
    """
    def test_GIVEN_outputmode_set_WHEN_read_then_logmessage_is_as_expected(self):
        self._write_output_mode(0)
        current_time = datetime.now().replace(year=1900, month=01, day=01)
        log_message_time = self._get_log_message_time(self.ca.get_pv_value("HFMAGPSU_01:LOGMESSAGE"))
        time_difference = current_time - log_message_time
        self.assertLess(time_difference.seconds, 3)

    def test_GIVEN_limit_set_WHEN_read_then_logmessage_is_as_expected(self):
        limit = 33.4
        self._write_limit(limit)
        current_time = datetime.now().replace(year=1900, month=01, day=01)
        log_message_time = self._get_log_message_time(self.ca.get_pv_value("HFMAGPSU_01:LOGMESSAGE"))
        time_difference = current_time - log_message_time
        self.assertLess(time_difference.seconds, 3)
