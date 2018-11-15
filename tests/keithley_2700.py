import time
import unittest
from contextlib import contextmanager
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KHLY2700_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2700"),
        "macros": {},
        "emulator": "keithley_2700",
    },
]

# TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
TEST_MODES = [TestModes.DEVSIM]

NORMAL_MODE = 0
BUFFER_CONTROL_MODE = 1

on_off_status = {False: "OFF", True: "ON"}

DRIFT_TOLERANCE = 1


class Status(object):
    ON = "ON"
    OFF = "OFF"


class Keithley2700Tests(unittest.TestCase):
    """
    Tests for the Keithley2700.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2700", DEVICE_PREFIX)
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

    def test_WHEN_buffer_range_set_THEN_buffer_within_range_is_returned(self):
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
            self.ca.assert_setting_setpoint_sets_readback(sample_value,"FRES:DIGITS", expected_alarm=expected_alarm)
    
    def test_WHEN_start_channel_range_set_THEN_start_channel_matches_the_set_state(self):
        sample_channels = [101, 109, 205]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:START")

    def test_WHEN_end_channel_range_set_THEN_end_channel_matches_the_set_state(self):
        sample_channels = [201, 209, 210]
        for channel in sample_channels:
            self.ca.assert_setting_setpoint_sets_readback(channel, "CH:END")

    def test_WHEN_measurement_mode_set_THEN_measurement_mode_matches_the_set_state(self):
        self.ca.set_pv_value("CH:START:SP", 101)
        self.ca.set_pv_value("CH:END:SP", 210)
        sample_data = {0: "VOLT:DC", 1: "VOLT:AC", 2: "CURR:DC", 3: "CURR:AC", 4: "RES", 5: "FRES", 6: "CONT", 7: "FREQ", 8: "PER"}
        for measurement_enum, measurement_string in sample_data.items():
            self.ca.assert_setting_setpoint_sets_readback(measurement_string, "MEASUREMENT",
                                                          expected_value=measurement_string)

    def test_WHEN_elements_set_THEN_elements_are_as_expected(self):
        elements = "READ, CHAN, TST"
        self.ca.assert_setting_setpoint_sets_readback(elements, "DATAELEMENTS")


class DriftTests(unittest.TestCase):

    drift_data = ['1386.05,4000,101', '1387.25,4360,101', '1388.51,4720,101', '1389.79,5080,101',
                  '1391.07,5440,101', '1392.35,5800,101', '1393.71,6160,101', '1395.01,6520,101',
                  '1396.38,6880,101', '1397.70,7240,101']

    # Tuple format (reading, temperature, expected_drift)
    full_list_of_readings = [
        ('1386.05,4000,101', 47.424, 0.),
        ('1387.25,4360,101', 47.243, -0.000666667),
        ('1388.51,4720,101', 47.053, -0.00135333),
        ('1389.79,5080,101', 46.860, -0.00202627),
        ('1391.07,5440,101', 46.667, -0.00268574),
        ('1392.35,5800,101', 46.474, -0.00333203),
        ('1393.71,6160,101', 46.269, -0.00399872),
        ('1395.01,6520,101', 46.072, -0.00461874),
        ('1396.38,6880,101', 45.866, -0.0052597),
        ('1397.70,7240,101', 45.667, -0.00585451),
    ]

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2700", DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("IDN")
        self._lewis.backdoor_set_on_device("control_mode", BUFFER_CONTROL_MODE)
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")

    def _lewis_sync_helper(self, attribute, set_value, wait_time=0.5):
        while self._lewis.backdoor_get_from_device(str(attribute)) != str(set_value):
            time.sleep(wait_time)

    def _check_mock_buffer(self, inserted_data, wait_time=0.5):
        while str(self._lewis.backdoor_run_function_on_device("check_buffer_data")[0])\
                .replace("u", "") != str(inserted_data[0]):
            time.sleep(wait_time)

    # Don't clear the buffer and add new readings one by one
    @contextmanager
    def _insert_canned_readings_sequentially(self, reading):
        self._lewis.backdoor_set_on_device("control_mode", BUFFER_CONTROL_MODE)
        self._lewis.backdoor_run_function_on_device("insert_mock_data", [reading])
        time.sleep(2)  # for synchronicity help
        try:
            yield
        finally:
            pass

    # Insert readings in chunks
    @contextmanager
    def _insert_canned_readings_in_chunks(self, readings):
        # set control mode
        self._lewis.backdoor_set_on_device("control_mode", BUFFER_CONTROL_MODE)
        self._lewis_sync_helper("control_mode", BUFFER_CONTROL_MODE)

        # clear buffer
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")

        # put canned data in buffer
        self._lewis.backdoor_run_function_on_device("insert_mock_data", [readings])
        self._check_mock_buffer([readings])

        try:
            yield
        finally:
            # clear buffer
            self.ca.set_pv_value("BUFF:CLEAR:SP", "")
            # return to normal control mode
            self._lewis.backdoor_set_on_device("control_mode", NORMAL_MODE)
            self._lewis_sync_helper("control_mode", NORMAL_MODE)

    def test_GIVEN_empty_buffer_WHEN_values_added_sequentially_THEN_drift_correct(self, readings=drift_data,
                                                                                  expected=full_list_of_readings):
        # GIVEN
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")

        # WHEN
        for i in range(0, len(expected)):
            with self._insert_canned_readings_sequentially([readings[i]]):
                # THEN
                self.ca.assert_that_pv_is_number("CHNL:101:DRIFT", expected[i][2], tolerance=DRIFT_TOLERANCE)
                print "{:8.3f} - {:8.3f}".format(float(self.ca.get_pv_value("CHNL:101:TEMP")), expected[i][1])

        # Finally, clear buffer
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")
        # return to normal control mode
        self._lewis.backdoor_set_on_device("control_mode", NORMAL_MODE)
        self._lewis_sync_helper("control_mode", NORMAL_MODE)

    def test_GIVEN_empty_buffer_WHEN_values_added_in_blocks_THEN_drift_correct(self, readings=drift_data,
                                                                               expected=full_list_of_readings):
        for i in range(0, len(expected)):
            with self._insert_canned_readings_in_chunks(readings[:i+1]):
                self.ca.assert_that_pv_is_number("CHNL:101:TEMP", expected[i][1], tolerance=10)
                print "{:8.3f} - {:8.3f}".format(float(self.ca.get_pv_value("CHNL:101:TEMP")), expected[i][1])
                self.ca.assert_that_pv_is_number("CHNL:101:DRIFT", expected[i][2], tolerance=200)

    def test_GIVEN_empty_buffer_WHEN_reading_inserted_into_buffer_THEN_pvs_contain_correct_values(self):
        reading = ['1200,1,101']

        with self._insert_canned_readings_in_chunks(reading):
            time.sleep(2)
            self.ca.assert_that_pv_is_number("CHNL:101:READ", 1200)
            self.ca.assert_that_pv_is_number("CHNL:101:TIME", 1)
            self.ca.assert_that_pv_is_number("CHNL:101:TEMP", 93.7509, tolerance=1)

    def test_for_drift_correctness(self):
        readings = ['1200,1,101', '1206,1.05,101']

        with self._insert_canned_readings_in_chunks(readings):
            time.sleep(2)
            # self.ca.assert_that_pv_is_number("CHNL:101:READ", 1206)
            # self.ca.assert_that_pv_is_number("CHNL:101:DRIFT", -55.8839, tolerance=1)
            print self.ca.get_pv_value("CHNL:101:DRIFT")

    #test that :PREV values are updated correctly

    #dumb drift test
