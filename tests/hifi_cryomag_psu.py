import unittest
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc


class Hifi_cryomag_psuTests(unittest.TestCase):


    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("hifi_cryomag_psu") # emulator name
        self.ca = ChannelAccess(default_timeout=10)
        self.ca.wait_for("HIFICRYOMAG_01:DIRECTION", timeout=10)

    def _write_direction(self, direction):
        self._lewis.backdoor_set_on_device("direction", direction)
        self.ca.set_pv_value("HIFICRYOMAG_01:DIRECTION", direction)

    def _write_output_mode(self, om):
        self._lewis.backdoor_set_on_device("outputMode", om)
        self.ca.set_pv_value("HIFICRYOMAG_01:OUTPUTMODE", om)

    def _write_ramp_target(self, rt):
        self._lewis.backdoor_set_on_device("rampTarget", rt)
        self.ca.set_pv_value("HIFICRYOMAG_01:RAMPTARGET", rt)

    def _write_heater_status(self, hs):
        self._lewis.backdoor_set_on_device("heaterStatus", hs)
        self.ca.set_pv_value("HIFICRYOMAG_01:HEATERSTATUS", hs)

    def _write_heater_value(self, hv):
        self._lewis.backdoor_set_on_device("heaterValue", hv)
        self.ca.set_pv_value("HIFICRYOMAG_01:HEATERVALUE", hv)

    def _write_max_target(self, mt):
        self._lewis.backdoor_set_on_device("maxTarget", mt)
        self.ca.set_pv_value("HIFICRYOMAG_01:MAX", mt)

    def _write_mid_target(self, mt):
        self._lewis.backdoor_set_on_device("midTarget", mt)
        self.ca.set_pv_value("HIFICRYOMAG_01:MID", mt)

    def _write_ramp_rate(self, rr):
        self._lewis.backdoor_set_on_device("rampRate", rr)
        self.ca.set_pv_value("HIFICRYOMAG_01:RAMPRATE", rr)

    def test_GIVEN_direction_set_WHEN_read_THEN_direction_is_as_expected(self):
        expected_direction = "+"
        self._write_direction(expected_direction)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:DIRECTION", expected_direction)

    def test_GIVEN_outputMode_set_WHEN_read_THEN_outputMode_is_as_expected(self):
        expected_mode_set = 1
        expected_mode = 'T'
        self.ca.set_pv_value("HIFICRYOMAG_01:OUTPUTMODE", expected_mode_set)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:OUTPUTMODE", expected_mode)

    def test_GIVEN_rampTarget_set_WHEN_read_THEN_rampTarget_is_as_expected(self):
        expected_rampTarget = '%'
        self._write_ramp_target(expected_rampTarget)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:RAMPTARGET", expected_rampTarget)

    def test_GIVEN_heaterStatus_set_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_heaterStatus = 'ON'
        self._write_heater_status(expected_heaterStatus)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:HEATERSTATUS", expected_heaterStatus)
    
    def test_GIVEN_midTarget_set_WHEN_read_THEN_midTarget_is_as_expected(self):
        expected_midTarget = 2
        self._write_mid_target(expected_midTarget)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:MID", expected_midTarget)

    def test_GIVEN_heaterValue_set_WHEN_read_THEN_heaterValue_is_as_expected(self):
        expected_heaterValue = 15.5
        self._write_heater_value(expected_heaterValue)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:HEATERVALUE", expected_heaterValue)

    def test_GIVEN_maxTarget_set_WHEN_read_THEN_maxTarget_is_as_expected(self):
        expected_maxTarget = 4
        self._write_max_target(expected_maxTarget)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:MAX", expected_maxTarget)
        
    def test_GIVEN_rampRate_set_WHEN_read_THEN_rampRate_is_as_expected(self):
        expected_rampRate = 0.25
        self._write_ramp_rate(expected_rampRate)
        self.ca.assert_that_pv_is("HIFICRYOMAG_01:RAMPRATE", expected_rampRate)
