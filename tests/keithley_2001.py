import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KHLY2001_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2001"),
        "macros": {},
        "emulator": "keithley_2001",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

on_off_status = {False: "OFF", True: "ON"}


class Status(object):
    ON = "ON"
    OFF = "OFF"


class Keithley_2001Tests(unittest.TestCase):
    """
    Tests for the Keithley_2001 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("IDN")

    def test_WHEN_scan_state_set_THEN_scan_state_matches_the_set_state(self):
        sample_data = {0: "INT", 1: "NONE"}
        for enum_value, string_value in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "SCAN:STATE", expected_value=string_value)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_delay_state_set_THEN_delay_state_matches_the_set_state(self):
        for enum_value, string_value in on_off_status.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "DELAYMODE", expected_value=string_value)

    def test_WHEN_source_set_THEN_source_matches_the_set_state(self):
        sample_data = {0: "IMM", 1: "TIM", 2: "MAN", 3: "BUS", 4: "EXT"}
        for enum_value, string_value in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "CONTROLSOURCE", expected_value=string_value)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_buffer_size_set_THEN_buffer_size_matches_the_set_state_AND_alarm_is_major(self):
        expected_alarm = "MAJOR"
        sample_data = [0, 70000]
        for sample_data in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(sample_data, "BUFF:SIZE", expected_alarm=expected_alarm)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_buffer_size_set_THEN_buffer_size_matches_the_set_state_AND_alarm_is_none(self):
        expected_alarm = "NO_ALARM"
        sample_data = [5500, 2]
        for sample_data in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(sample_data, "BUFF:SIZE", expected_alarm=expected_alarm)

    def test_WHEN_buffer_feed_set_THEN_buffer_feed_matches_the_set_state(self):
        sample_data = {0: "SENS", 1: "CALC", 2: "NONE"}
        for enum_value, string_value in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "BUFF:SOURCE", expected_value=string_value)

    def test_WHEN_init_state_set_THEN_init_state_matches_the_set_state(self):
        for enum_value, string_value in on_off_status.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "INITMODE", expected_value=string_value)

    def test_WHEN_buffer_control_set_THEN_buffer_control_matches_the_set_state(self):
        sample_data = {0: "NEXT", 1: "ALW", 2: "NEV"}
        for enum_value, string_value in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "BUFF:CONTROLMODE", expected_value=string_value)

    def test_WHEN_buffer_range_set_then_buffer_within_range_is_returned(self):
        self._lewis.backdoor_set_on_device("buffer_range_readings", 10)
        self.ca.set_pv_value("CH:START", 2)
        self.ca.set_pv_value("COUNT", 4)
        self.ca.process_pv("BUFF:READ")
        expected_string = self.ca.get_pv_value("BUFF:READ")
        self.assertNotEquals(expected_string, "[]")

    def test_WHEN_sample_count_set_THEN_sample_count_matches_the_set_state_AND_within_alarm_is_major(self):
        expected_alarm = "MAJOR"
        sample_data = [0, 70000]
        for set_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(set_value, "SAMPLECOUNT", expected_alarm=expected_alarm)

    def test_WHEN_sample_count_set_THEN_sample_count_matches_the_set_state_AND_within_alarm_is_none(self):
        expected_alarm = "NO_ALARM"
        sample_data = [2, 55000]
        for enum_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "SAMPLECOUNT", expected_value=enum_value,
                                                          expected_alarm=expected_alarm)

    def test_WHEN_cycles_rate_set_THEN_cycle_rate_matches_the_set_state_AND_within_alarm_is_major(self):
        expected_alarm = "MAJOR"
        sample_data = [0, 65.0]
        for set_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(set_value, "FRES:NPLC", expected_alarm=expected_alarm)

    def test_WHEN_cycles_rate_set_THEN_cycle_rate_matches_the_set_state_AND_within_alarm_is_none(self):
        expected_alarm = "NO_ALARM"
        sample_data = [0.1, 2.0]
        for enum_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "FRES:NPLC", expected_value=enum_value,
                                                          expected_alarm=expected_alarm)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_buffer_state_set_THEN_buffer_state_matches_the_set_state(self):
        for enum_value, string_value in on_off_status.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "DELAYMODE", expected_value=string_value)

    def test_WHEN_auto_range_set_THEN_auto_range_matches_the_set_state(self):
        for enum_value, expected_state in on_off_status.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "FRES:AUTORANGE", expected_value=expected_state)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_time_stamp_set_to_absolute_THEN_time_stamp_matches_the_set_state(self):
        sample_data = {0: "ABS", 1: "DELT"}
        for enum_value, expected_state in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(enum_value, "TIME:FORMAT", expected_value=expected_state)

    def test_WHEN_fres_digits_set_THEN_fres_digits_matches_the_set_state_AND_alarm_is_major(self):
        expected_alarm = "MAJOR"
        sample_data = [3, 8, 10]
        for sample_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(sample_value, "FRES:DIGITS", expected_alarm=expected_alarm)

    def test_WHEN_fres_digits_set_THEN_fres_digits_matches_the_set_state_AND_alarm_is_none(self):
        expected_alarm = "NO_ALARM"
        sample_data = [4, 6]
        for sample_value in sample_data:
            self.ca.assert_setting_setpoint_sets_readback(sample_value, "FRES:DIGITS", expected_alarm=expected_alarm)

    def test_WHEN_start_channel_range_set_THEN_start_channel_matches_the_set_state(self):
        sample_channels = [101, 109, 205]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:START")

    def test_WHEN_end_channel_range_set_THEN_end_channel_matches_the_set_state(self):
        sample_channels = [201, 209, 210]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:END")

    def test_WHEN_measurement_mode_set_THEN_mesaurement_mode_matches_the_set_state(self):
        self.ca.set_pv_value("CH:START:SP", 101)
        self.ca.set_pv_value("CH:END:SP", 210)
        sample_data = {0: "VOLT:DC", 1: "VOLT:AC", 2: "CURR:DC", 3: "CURR:AC", 4: "RES", 5: "FRES", 6: "CONT",
                       7: "FREQ", 8: "PER"}
        for measurement_enum, measurement_string in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(measurement_string, "MEASUREMENT",
                                                          expected_value=measurement_string)

    def test_WHEN_elements_set_THEN_elements_are_as_expected(self):
        elements = "READ, CHAN, TST"
        self.ca.assert_setting_setpoint_sets_readback(elements, "DATAELEMENTS")

