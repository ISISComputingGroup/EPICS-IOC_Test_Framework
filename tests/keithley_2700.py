import unittest
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
import time

DEVICE_PREFIX = "KHLY2700_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2700"),
        "macros": {},
        "emulator": "keithley_2700",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Status(object):
    ON = "ON"
    OFF = "OFF"


class Keithley_2700Tests(unittest.TestCase):
    """
    Tests for the Keithley2700.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2700", DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca.wait_for("IDN")

    def test_GIVEN_scan_state_set_WHEN_read_THEN_scan_state_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["INT", "NONE"]
        for set_value, expected_value in zip(sample_data, expected_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "SCAN:STATE", "SCAN:STATE:SP", expected_value)

    def test_GIVEN_idn_defined_WHEN_read_THEN_idn_is_as_expected(self):
        self.ca.assert_that_pv_is("IDN", "Keithley 2700 Emulator IDN")

    def test_GIVEN_delay_state_set_WHEN_read_THEN_delay_state_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["OFF", "ON"]
        for set_value, expected_value in zip(sample_data, expected_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "DELAYMODE", "DELAYMODE:SP", expected_value)

    def test_GIVEN_source_set_WHEN_read_THEN_source_is_as_expected(self):
        sample_data = [0, 1, 2, 3, 4]
        expected_channel = ["IMM", "TIM", "MAN", "BUS", "EXT"]
        for set_value, expected_value in zip(sample_data, expected_channel):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "CONTROLSOURCE", "CONTROLSOURCE:SP",
                                                          expected_value)

    def test_GIVEN_buffer_size_set_WHEN_read_THEN_buffer_size_is_as_expected_AND_within_range(self):
        expected_buffer_size = [5500, 0, 2, 70000]
        alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
                       ChannelAccess.ALARM_MAJOR]
        for set_value, expected_alarm in zip(expected_buffer_size, alarm_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "BUFFER:SIZE", "BUFFER:SIZE:SP",
                                                          set_value, expected_alarm=expected_alarm)

    def test_GIVEN_buffer_feed_set_WHEN_read_THEN_buffer_feed_is_as_expected(self):
        sample_data = [0, 1, 2]
        expected_channel = ["SENS", "CALC", "NONE"]
        for set_value, expected_value in zip(sample_data, expected_channel):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "BUFFER:SOURCE", "BUFFER:SOURCE:SP",
                                                          expected_value)

    def test_GIVEN_init_state_set_WHEN_read_THEN_init_state_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["ON", "OFF"]
        for set_value, expected_value in zip(sample_data, expected_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "INITMODE", "INITMODE:SP", expected_value)

    def test_GIVEN_buffer_control_set_WHEN_read_THEN_buffer_control_is_as_expected(self):
        sample_data = [0, 1, 2]
        expected_channel = ["NEXT", "ALW", "NEV"]
        for set_value, expected_value in zip(sample_data, expected_channel):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "BUFFER:CONTROLMODE", "BUFFER:CONTROLMODE:SP",
                                                          expected_value)

    def test_GIVEN_buffer_range_set_WHEN_read_then_buffer_within_range_is_returned(self):
        self._lewis.backdoor_set_on_device("buffer_range_readings", 10)
        self.ca.set_pv_value("CH:START", 2)
        self.ca.set_pv_value("COUNT", 4)
        self.ca.set_pv_value("BUFFER:READINGS.PROC", 1)
        expected_string = self.ca.get_pv_value("BUFFER:READINGS")
        self.assertNotEquals(expected_string, "[]")

    def test_GIVEN_sample_count_set_WHEN_read_THEN_sample_count_is_as_expected_AND_within_range(self):
        expected_sample_count = [2, 0, 5500, 70000]
        alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
                       ChannelAccess.ALARM_MAJOR]
        for set_value, expected_alarm in zip(expected_sample_count, alarm_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "SAMPLECOUNT", "SAMPLECOUNT:SP", set_value,
                                                          expected_alarm=expected_alarm)

    def test_GIVEN_cycles_rate_set_WHEN_read_THEN_cycle_rate_is_as_expected_AND_within_range(self):
        expected_cycles = [0.1, 0, 2.0, 65.0]
        alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
                       ChannelAccess.ALARM_MAJOR]
        for set_value, expected_alarm in zip(expected_cycles, alarm_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "FRES:NPLC", "FRES:NPLC:SP", set_value,
                                                          expected_alarm=expected_alarm)

    def test_GIVEN_buffer_state_set_WHEN_read_THEN_buffer_state_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["OFF", "ON"]
        for set_value, expected_value in zip(sample_data, expected_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "DELAYMODE", "DELAYMODE:SP", expected_value)

    def test_GIVEN_auto_range_set_WHEN_read_THEN_auto_range_is_as_expected(self):
        sample_data = [0, 1]
        expected_data = ["ON", "OFF"]
        for set_value, expected_state in zip(sample_data, expected_data):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "FRES:AUTORANGE", "FRES:AUTORANGE:SP",
                                                          expected_state)

    def test_GIVEN_time_stamp_set_to_absolute_WHEN_read_THEN_time_stamp_is_as_expected(self):
        sample_data = [0, 1]
        expected_data = ["ABS", "DELT"]
        for set_value, expected_state in zip(sample_data, expected_data):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "TIMESTAMP:FORMAT", "TIMESTAMP:FORMAT:SP",
                                                          expected_state)

    def test_GIVEN_fres_digits_set_WHEN_read_THEN_fres_digits_is_as_expected_AND_within_range(self):
        expected_sample_count = [3, 5, 8]
        alarm_state = [ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
                       ChannelAccess.ALARM_MAJOR]
        for set_value, alarm_state in zip(expected_sample_count, alarm_state):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "FRES:DIGITS:SP",
                                                          "FRES:DIGITS", set_value,
                                                          expected_alarm=alarm_state)

    def test_GIVEN_start_channel_range_set_WHEN_read_THEN_start_channel_is_as_expected(self):
        sample_channels = [101, 109, 205]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:START", "CH:START:SP", channel)

    def test_GIVEN_end_channel_range_set_WHEN_read_THEN_end_channel_is_as_expected(self):
        sample_channels = [201, 209, 210]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:END", "CH:END:SP", channel)

    def test_GIVEN_measurement_mode_set_WHEN_read_THEN_mesaurement_mode_is_as_expected(self):
        measurement_enums = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        self.ca.set_pv_value("CH:START:SP", 101)
        self.ca.set_pv_value("CH:END:SP", 210)
        measurement_strings = ["VOLT", "VOLT:AC", "CURR", "CURR:AC", "RES", "FRES", "CONT", "FREQ", "PER"]
        for measurement_string, measurement_enum in zip(measurement_strings, measurement_enums):
            self.ca.assert_setting_setpoint_sets_readback(measurement_enum, "MEASUREMENT",
                                                          "MEASUREMENT:SP", measurement_string)

    def test_GIVEN_buffer_autoclear_mode_set_WHEN_read_THEN_autoclear_mode_is_as_expected(self):
        sample_data = [0, 1]
        expected_data = ["ON", "OFF"]
        for set_value, expected_state in zip(sample_data, expected_data):
            self.ca.assert_setting_setpoint_sets_readback(set_value, "BUFFER:CLEAR:AUTO", "BUFFER:CLEAR:AUTO:SP",
                                                          expected_state)

    def test_GIVEN_elements_set_WHEN_read_THEN_elements_are_as_expected(self):
        elements = "READ, CHAN, TST"
        self.ca.assert_setting_setpoint_sets_readback(elements, "DATAELEMENTS", "DATAELEMENTS:SP", elements)