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

DRIFT_TOLERANCE = 0.1
TEMP_TOLERANCE = 0.1
TIME_TOLERANCE = 0
READ_TOLERANCE = 0.5


class Status(object):
    ON = "ON"
    OFF = "OFF"


class SetUpTests(unittest.TestCase):
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
        sample_data = [-1, 0, 55001, 70000]
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


class BufferTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2700", DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("IDN")
        self._lewis.backdoor_set_on_device("control_mode", BUFFER_CONTROL_MODE)
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")
        self.ca.assert_that_pv_is("BUFF:AUTOCLEAR", "ON")

    def _generate_readings(self, num_readings_gen, time_between):
        min_r = 1000
        max_r = 2000
        start_time = 1
        channels = [c for c in range(101, 110 + 1)] + [c for c in range(201, 210 + 1)]
        readings = []

        for i in range(num_readings_gen):
            resistance = min_r + i
            while resistance > max_r:
                resistance = resistance - min_r
            time_stamp = start_time + (i*time_between)
            channel = channels[i % 20]
            readings.append(str(resistance) + "," + str(time_stamp) + "," + str(channel))

        return readings

    @contextmanager
    def _insert_reading(self, reading):
        self._lewis.backdoor_run_function_on_device("insert_mock_data", [reading])
        time.sleep(0.5)  # for synchronicity help
        try:
            yield
        finally:
            pass

    def test_GIVEN_buffer_full_WHEN_buffer_clears_THEN_buffer_still_used(self):
        buffer_test_size = 5
        self.ca.set_pv_value("BUFF:SIZE:SP", buffer_test_size)
        self.ca.assert_that_pv_is("BUFF:SIZE", buffer_test_size)
        reads = self._generate_readings(10, 5)

        self.ca.assert_that_pv_is("BUFF:CONTROLMODE", "ALW")  # indicative that buffer is being written to
        # GIVEN
        with self._insert_reading(reads[:5]):
            self.ca.assert_that_pv_is("BUFF:NEXT", 0)  # indicative that buffer is now full

        # WHEN
        with self._insert_reading([reads[6]]):
            self.ca.assert_that_pv_is("BUFF:NEXT", 1)  # Reading was inserted to buffer
            # THEN
            self.ca.assert_that_pv_is("BUFF:CONTROLMODE", "ALW")

    def test_GIVEN_full_buffer_THEN_next_buff_location_reports_0(self):
        buffer_test_size = 10
        self.ca.set_pv_value("BUFF:SIZE:SP", buffer_test_size)
        self.ca.assert_that_pv_is("BUFF:SIZE", buffer_test_size)
        reads = self._generate_readings(10, 5)
        # GIVEN
        with self._insert_reading(reads[:10]):
            pass

        # THEN
        self.ca.assert_that_pv_is("BUFF:NEXT", 0)

    def test_GIVEN_buffer_full_THEN_buffer_clears(self):
        buffer_test_size = 50  # buffer 0 indexed, so there are 50 buffer locations, 0-49
        # GIVEN
        # Use smaller buffer to speed up test
        self.ca.set_pv_value("BUFF:SIZE:SP", buffer_test_size)
        self.ca.assert_that_pv_is("BUFF:SIZE", buffer_test_size)
        reads = self._generate_readings(60, 5)  # 10 greater than buffer capacity

        with self._insert_reading(reads[:49]):
            pass  # Now 0-48 are occupied (49 readings), only index 49 is empty
        self.ca.assert_that_pv_is("BUFF:NEXT", 49)

        with self._insert_reading([reads[50]]):
            pass
        self.ca.assert_that_pv_is("BUFF:NEXT", 0)

        with self._insert_reading([reads[51]]):
            pass
        self.ca.assert_that_pv_is("BUFF:NEXT", 1)


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2700", DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("IDN")
        self._lewis.backdoor_set_on_device("control_mode", BUFFER_CONTROL_MODE)
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")
        self.ca.assert_that_pv_is("BUFF:AUTOCLEAR", "ON")

    @contextmanager
    def _insert_reading(self, reading):
        self._lewis.backdoor_run_function_on_device("insert_mock_data", [reading])
        time.sleep(0.5)  # for synchronicity help
        try:
            yield
        finally:
            pass

    def test_GIVEN_empty_buffer_WHEN_reading_inserted_THEN_channel_PVs_get_correct_values(self):
        reading_on_channel_101 = "1386.05,4000,101"
        reading_on_channel_103 = "1386.05,4000,103"
        expected_values = {
            'read':  1386.05,
            'time':  4000,
            'temp':  47.424,
            'drift': 0,
        }
        # GIVEN
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")
        # WHEN
        with self._insert_reading([reading_on_channel_101]):
            # THEN
            self.ca.assert_that_pv_is_number("CHNL:101:READ", expected_values['read'], tolerance=READ_TOLERANCE)
            self.ca.assert_that_pv_is_number("CHNL:101:TIME", expected_values['time'], tolerance=TIME_TOLERANCE)
            self.ca.assert_that_pv_is_number("CHNL:101:TEMP", expected_values['temp'], tolerance=TEMP_TOLERANCE)
            self.ca.assert_that_pv_is_number("CHNL:101:DRIFT", expected_values['drift'], tolerance=DRIFT_TOLERANCE)
        with self._insert_reading([reading_on_channel_103]):
            # THEN
            self.ca.assert_that_pv_is_number("CHNL:103:READ", expected_values['read'], tolerance=READ_TOLERANCE)
            self.ca.assert_that_pv_is_number("CHNL:103:TIME", expected_values['time'], tolerance=TIME_TOLERANCE)
            self.ca.assert_that_pv_is_number("CHNL:103:TEMP", expected_values['temp'], tolerance=TEMP_TOLERANCE)
            self.ca.assert_that_pv_is_number("CHNL:103:DRIFT", expected_values['drift'], tolerance=DRIFT_TOLERANCE)


class DriftTests(unittest.TestCase):
    # Tuple format (reading, temperature, expected_drift)
    drift_test_data = [
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

    # Don't clear the buffer and add new readings one by one
    @contextmanager
    def _insert_reading(self, reading):
        self._lewis.backdoor_set_on_device("control_mode", BUFFER_CONTROL_MODE)
        self._lewis.backdoor_run_function_on_device("insert_mock_data", [reading])
        time.sleep(0.5)  # for synchronicity help
        try:
            yield
        finally:
            pass

    def test_GIVEN_empty_buffer_WHEN_values_added_THEN_temp_AND_drift_correct(self, test_data=drift_test_data):
        readings = [r[0] for r in test_data]  # extract reading strings from test data to insert to buffer
        # GIVEN
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")
        # WHEN
        for i in range(0, len(test_data)):
            with self._insert_reading([readings[i]]):
                # THEN
                self.ca.assert_that_pv_is_number("CHNL:101:DRIFT", test_data[i][2], tolerance=DRIFT_TOLERANCE)
                self.ca.assert_that_pv_is_number("CHNL:101:TEMP", test_data[i][1], tolerance=TEMP_TOLERANCE) # TODO 0.1K

        # Finally, clear buffer
        self.ca.set_pv_value("BUFF:CLEAR:SP", "")
        # return to normal control mode
        self._lewis.backdoor_set_on_device("control_mode", NORMAL_MODE)
        self._lewis_sync_helper("control_mode", NORMAL_MODE)

