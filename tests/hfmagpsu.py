import unittest
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc

class HfmagpsuTests(unittest.TestCase):


    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("HFMAGPSU") # emulator name
        self.ca = ChannelAccess(default_timeout=10)
        self.ca.wait_for("HFMAGPSU_01:DIRECTION", timeout=10)

    def _write_direction(self, direction):
        self._lewis.backdoor_set_on_device("direction", direction)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS DIRECTION: [" + str(direction) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:DIRECTION:SP", direction)

    def _write_output_mode(self, om):
        self._lewis.backdoor_set_on_device("outputMode", om)
        self.ca.set_pv_value("HFMAGPSU_01:OUTPUTMODE:SP", om)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS UNITS: [" + str(om) + "]")

    def _write_ramp_target(self, rt):
        self._lewis.backdoor_set_on_device("rampTarget", rt)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS RAMP TARGET: [" + str(rt) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:RAMPTARGET:SP", rt)

    def _write_heater_status(self, hs):
        self._lewis.backdoor_set_on_device("heaterStatus", hs)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS HEATER STATUS: [" + str(hs) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:HEATERSTATUS:SP", hs)

    def _write_heater_value(self, hv):
        self._lewis.backdoor_set_on_device("heaterValue", hv)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS HEATER OUTPUT: [" + str(hv) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:HEATERVALUE:SP", hv)

    def _write_max_target(self, max):
        self._lewis.backdoor_set_on_device("maxTarget", max)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS MAX SETTING: [" + str(max) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:MAX:SP", max)

    def _write_mid_target(self, mid):
        self._lewis.backdoor_set_on_device("midTarget", mid)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS MID SETTING: [" + str(mid) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:MID:SP", mid)

    def _write_ramp_rate(self, rr):
        self._lewis.backdoor_set_on_device("rampRate", rr)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS RAMP RATE: [" + str(rr) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:RAMPRATE:SP", rr)

    def _write_pause(self, p):
        self._lewis.backdoor_set_on_device("pause", p)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS PAUSE STATUS: [" + str(p) + "]")
        self.ca.set_pv_value("HFMAGPSU_01:PAUSE:SP", p)

    def _write_limit(self, l):
        self._lewis.backdoor_set_on_device("limit", l)
        self.ca.set_pv_value("HFMAGPSU_01:LIMIT:SP", l)
        self.ca.set_pv_value("HFMAGPSU_01:LOGMESSAGE", "HH:MM:SS VOLTAGE LIMIT: [" + str(l) + "]")

    def test_GIVEN_midTarget_set_WHEN_read_THEN_midTarget_is_as_expected(self):
        expected_midTarget = 2.0
        self._write_mid_target(expected_midTarget)
        self.ca.assert_that_pv_is("HFMAGPSU_01:MID", expected_midTarget)
    
    def test_GIVEN_rampRate_set_WHEN_read_THEN_rampRate_is_as_expected(self):
        expected_rampRate = 0.25
        self._write_ramp_rate(expected_rampRate)
        self.ca.assert_that_pv_is("HFMAGPSU_01:RAMPRATE", expected_rampRate)
    
    def test_GIVEN_maxTarget_set_WHEN_read_THEN_maxTarget_is_as_expected(self):
        expected_maxTarget = 4.0
        self._write_max_target(expected_maxTarget)
        self.ca.assert_that_pv_is("HFMAGPSU_01:MAX", expected_maxTarget)  
        
    def test_GIVEN_limit_set_WHEN_read_THEN_limit_is_as_expected(self):
        expected_output = 35.5
        self._write_limit(expected_output)
        self.ca.assert_that_pv_is("HFMAGPSU_01:LIMIT", expected_output)

    def test_GIVEN_heaterValue_set_WHEN_read_THEN_heaterValue_is_as_expected(self):
        expected_heaterValue = 15.5
        self._write_heater_value(expected_heaterValue)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERVALUE", expected_heaterValue)
        
    def test_GIVEN_pause_set_WHEN_read_THEN_pause_is_as_expected(self):
        expected_output = 'ON'
        self._write_pause(1)
        self.ca.assert_that_pv_is("HFMAGPSU_01:PAUSE", expected_output)

    def test_GIVEN_outputMode_set_WHEN_read_THEN_outputMode_is_as_expected(self):
        expected_mode_str = 'TESLA'
        self._write_output_mode(1)
        self.ca.assert_that_pv_is("HFMAGPSU_01:OUTPUTMODE", expected_mode_str)

    def test_GIVEN_heaterStatus_set_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_heaterStatus = 'ON'
        self._write_heater_status(1)
        self.ca.assert_that_pv_is("HFMAGPSU_01:HEATERSTATUS", expected_heaterStatus)

    def test_GIVEN_outputmode_set_WHEN_read_then_logmessage_is_as_expected(self):
        self._write_output_mode(0)
        expected_message = "HH:MM:SS UNITS: [0]"
        self.ca.assert_that_pv_is("HFMAGPSU_01:LOGMESSAGE", expected_message)  

    def test_GIVEN_limit_set_WHEN_read_then_logmessage_is_as_expected(self):
        self._write_limit(33.4)
        expected_message = "HH:MM:SS VOLTAGE LIMIT: [33.4]"
        self.ca.assert_that_pv_is("HFMAGPSU_01:LOGMESSAGE", expected_message)

    def test_GIVEN_rampTarget_set_WHEN_read_THEN_rampTarget_is_as_expected(self):
        expected_rampTarget = 'MAX'
        self._write_ramp_target(2)
        self.ca.assert_that_pv_is("HFMAGPSU_01:RAMPTARGET", expected_rampTarget)

    def test_GIVEN_direction_set_WHEN_read_THEN_direction_is_as_expected(self):
        expected_direction = '+'
        self._write_direction(2)
        self.ca.assert_that_pv_is("HFMAGPSU_01:DIRECTION", expected_direction)
