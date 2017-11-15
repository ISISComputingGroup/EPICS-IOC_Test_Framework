import unittest
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from datetime import datetime, date, timedelta


class HfmagpsuTests(unittest.TestCase):


    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("HFMAGPSU") # emulator name
        self.ca = ChannelAccess(default_timeout=10)
        self.ca.wait_for("HFMAGPSU_01:DIRECTION", timeout=10)

    ''' Retrieve time from the log message PV and parse to a datetime object '''

    def get_log_message_time(self, log_message):
        time_string = log_message[:8]
        time_object = datetime.strptime(time_string, '%H:%M:%S')
        return time_object

    def test_GIVEN_midTarget_set_WHEN_read_THEN_midTarget_is_as_expected(self):
        test_value = 2.325
        self.ca.set_pv_value("HFMAGPSU_01:MID:SP", test_value)
        self.ca.assert_that_pv_is("HFMAGPSU_01:MID", test_value)

    def test_GIVEN_rampRate_set_WHEN_read_THEN_rampRate_is_as_expected(self):
        test_value = 0.51
        self.ca.set_pv_value("HFMAGPSU_01:RAMPRATE:SP", test_value)
        self.ca.assert_that_pv_is("HFMAGPSU_01:RAMPRATE", test_value)

    def test_GIVEN_maxTarget_set_WHEN_read_THEN_maxTarget_is_as_expected(self):
        test_value = 4.0
        self.ca.set_pv_value("HFMAGPSU_01:MAX:SP", test_value)
        self.ca.assert_that_pv_is("HFMAGPSU_01:MAX", test_value)

    def test_GIVEN_limit_set_WHEN_read_THEN_limit_is_as_expected(self):
        test_value = 35.5
        self.ca.set_pv_value("HFMAGPSU_01:LIMIT:SP", test_value)
        self.ca.assert_that_pv_is("HFMAGPSU_01:LIMIT", test_value)

    def test_GIVEN_constant_set_WHEN_read_THEN_constant_is_as_expected(self):
        test_value = 0.0032
        self.ca.set_pv_value("HFMAGPSU_01:CONSTANT:SP", test_value)
        self.ca.assert_that_pv_is("HFMAGPSU_01:CONSTANT", test_value)

    def test_GIVEN_heaterValue_set_WHEN_read_THEN_heaterValue_is_as_expected(self):
        test_value = 15.5
        self.ca.set_pv_value("HFMAGPSU_01:HEATERVALUE:SP", test_value)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERVALUE", test_value)

    def test_GIVEN_pause_set_ON_WHEN_read_THEN_pause_is_as_expected(self):
        expected_output = 'ON'
        self.ca.set_pv_value("HFMAGPSU_01:PAUSE:SP", 1)
        self.ca.assert_that_pv_is("HFMAGPSU_01:PAUSE", expected_output)

    def test_GIVEN_pause_set_OFF_WHEN_read_THEN_pause_is_as_expected(self):
        expected_output = 'OFF'
        self.ca.set_pv_value("HFMAGPSU_01:PAUSE:SP", 0)
        self.ca.assert_that_pv_is("HFMAGPSU_01:PAUSE", expected_output)

    def test_GIVEN_outputMode_set_AMPS_WHEN_read_THEN_outputMode_is_as_expected(self):
        test_value = 'AMPS'
        self.ca.set_pv_value("HFMAGPSU_01:OUTPUTMODE:SP", 0)
        self.ca.assert_that_pv_is("HFMAGPSU_01:OUTPUTMODE", test_value)

    def test_GIVEN_outputMode_set_TESLA_WHEN_read_THEN_outputMode_is_as_expected(self):
        test_value = 'TESLA'
        self.ca.set_pv_value("HFMAGPSU_01:OUTPUTMODE:SP", 1)
        self.ca.assert_that_pv_is("HFMAGPSU_01:OUTPUTMODE", test_value)

    def test_GIVEN_heaterStatus_set_ON_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_heaterStatus = 'ON'
        self.ca.set_pv_value("HFMAGPSU_01:HEATERSTATUS:SP", 1)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERSTATUS", expected_heaterStatus)

    def test_GIVEN_heaterStatus_set_OFF_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_heaterStatus = 'OFF'
        self.ca.set_pv_value("HFMAGPSU_01:HEATERSTATUS:SP", 0)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERSTATUS", expected_heaterStatus)

    def test_GIVEN_rampTarget_set_WHEN_read_THEN_rampTarget_is_as_expected(self):
        ramp_targets = ['ZERO', 'MID', 'MAX']
        for index, value in enumerate(ramp_targets):
            self.ca.set_pv_value("HFMAGPSU_01:RAMPTARGET:SP", index)
            expected_target = value
            self.ca.assert_that_pv_is("HFMAGPSU_01:RAMPTARGET", expected_target)

    def test_GIVEN_direction_set_WHEN_read_THEN_direction_is_as_expected(self):
        directions = ["0", "-", "+"]
        for index, value in enumerate(directions):
            self.ca.set_pv_value("HFMAGPSU_01:DIRECTION:SP", index)
            expected_direction = value
            self.ca.assert_that_pv_is("HFMAGPSU_01:DIRECTION", expected_direction)
    '''
     As the log message contains a timestamp and the setpoint/test timestamps will differ
     by a few seconds, we're testing to see if the timestamp difference is within 4 seconds.
    '''
    def test_GIVEN_outputmode_set_WHEN_read_then_logmessage_is_as_expected(self):
        self.ca.set_pv_value("HFMAGPSU_01:OUTPUTMODE:SP", 0)
        current_time = datetime.now().replace(year=1900, month=01, day=01)
        log_message_time = self.get_log_message_time(self.ca.get_pv_value("HFMAGPSU_01:LOGMESSAGE"))
        time_difference = current_time - log_message_time
        self.assertLess(time_difference.seconds, 4)

    def test_GIVEN_limit_set_WHEN_read_then_logmessage_is_as_expected(self):
        test_value = 33.4
        self.ca.set_pv_value("HFMAGPSU_01:LIMIT:SP", test_value)
        current_time = datetime.now().replace(year=1900, month=01, day=01)
        log_message_time = self.get_log_message_time(self.ca.get_pv_value("HFMAGPSU_01:LOGMESSAGE"))
        time_difference = current_time - log_message_time
        self.assertLess(time_difference.seconds, 4)
