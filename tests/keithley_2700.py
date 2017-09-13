import unittest
from unittest import skipIf
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister



class Keithley_2700Tests(unittest.TestCase):
    """
    Tests for the Keithley2700.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2700")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.wait_for("KHLY2700_01:IDN")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_idn_defined_WHEN_read_THEN_idn_is_as_expected(self):
        self.ca.assert_that_pv_is("KHLY2700_01:IDN", "Keithley 2700 Multimeter emulator.")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_available_AND_reserved_bytes_set_WHEN_read_THEN_staTus_of_memory_is_as_expected(self):
        self.ca.set_pv_value("KHLY2700_01:BUFFER_SIZE:SP", 100)
        self._lewis.backdoor_set_on_device("buffer_readings", 10)
        self._lewis.backdoor_set_on_device("buffer", 100)
        self.ca.assert_that_pv_is("KHLY2700_01:BUFFER_SIZE.", 100)
        self.ca.set_pv_value("KHLY2700_01:BUFFER_STATS.PROC", 1)
        self.ca.assert_that_pv_is("KHLY2700_01:BUFFER_STATS", "92160 bytes,10240 bytes")

    def test_GIVEN_source_set_WHEN_read_THEN_source_is_as_expected(self):
        sample_data = [0, 1, 2, 3, 4]
        expected_channel = ["IMM", "EXT", "TIM", "MAN", "BUS"]
        for input, output in zip(sample_data, expected_channel):
            self.ca.set_pv_value("KHLY2700_01:CONTROL_SOURCE:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:CONTROL_SOURCE", output)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_delay_state_set_WHEN_read_THEN_delay_state_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["OFF", "ON"]
        for input, output in zip(sample_data, expected_state):
            self.ca.set_pv_value("KHLY2700_01:DELAY_STATE:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:DELAY_STATE", output)

    def test_GIVEN_buffer_size_set_WHEN_read_THEN_buffer_size_is_as_expected_AND_within_range(self):

        expected_buffer_size = [5500, 0, 2, 70000]
        alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
                            ChannelAccess.ALARM_MAJOR]
        for input, output in zip(expected_buffer_size, alarm_state):
            self.ca.set_pv_value("KHLY2700_01:BUFFER_SIZE:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:BUFFER_SIZE", input)
            self.ca.assert_pv_alarm_is("KHLY2700_01:BUFFER_SIZE", output)

    def test_GIVEN_buffer_feed_set_WHEN_read_THEN_buffer_feed_is_as_expected(self):
        sample_data = [0, 1, 2]
        expected_channel = ["SENS", "CALC", "NONE"]
        for input, output in zip(sample_data, expected_channel):
            self.ca.set_pv_value("KHLY2700_01:BUFFER_FEED:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:BUFFER_FEED", output)

    def test_GIVEN_scan_state_set_WHEN_read_THEN_scan_state_is_as_expected(self):
         sample_data = [0, 1]
         expected_state = ["NONE", "INT"]
         for input, output in zip(sample_data, expected_state):
            self.ca.set_pv_value("KHLY2700_01:SCAN_STATE:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:SCAN_STATE", output)

    def test_GIVEN_init_state_set_WHEN_read_THEN_init_state_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["ON", "OFF"]
        for input, output in zip(sample_data, expected_state):
            self.ca.set_pv_value("KHLY2700_01:INIT:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:INIT", output)

    def test_GIVEN_buffer_control_set_WHEN_read_THEN_buffer_control_is_as_expected(self):
        sample_data = [0, 1, 2]
        expected_channel = ["NEXT", "ALW", "NEV"]
        for input, output in zip(sample_data, expected_channel):
            self.ca.set_pv_value("KHLY2700_01:BUFFER_CONTROL:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:BUFFER_CONTROL", output)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_buffer_range_set_WHEN_read_then_buffer_within_range_is_returned(self):
        self._lewis.backdoor_set_on_device("buffer_readings", 10)
        self.ca.set_pv_value("KHLY2700_01:START", 2)
        self.ca.set_pv_value("KHLY2700_01:COUNT", 4)
        self.ca.set_pv_value("KHLY2700_01:LIST_OF_READINGS.PROC", 1)
        expected_string = self.ca.get_pv_value("KHLY2700_01:LIST_OF_READINGS")
        self.assertNotEquals(expected_string, "[]")

    def test_GIVEN_sample_count_set_WHEN_read_THEN_sample_count_is_as_expected_AND_within_range(self):
        expected_sample_count = [2, 0, 5500, 70000]
        alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
                           ChannelAccess.ALARM_MAJOR]
        for input, output in zip(expected_sample_count, alarm_state):
            self.ca.set_pv_value("KHLY2700_01:SAMPLE_COUNT:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:SAMPLE_COUNT", input)
            self.ca.assert_pv_alarm_is("KHLY2700_01:SAMPLE_COUNT", output)

    def test_GIVEN_cycles_rate_set_WHEN_read_THEN_cycle_rate_is_as_expected_AND_within_range(self):
         expected_cycles = [0.1, 0, 2.0, 65.0]
         alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
                            ChannelAccess.ALARM_MAJOR]
         for input, output in zip(expected_cycles, alarm_state):
            self.ca.set_pv_value("KHLY2700_01:NPLCYCLES:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:NPLCYCLES", input)
            self.ca.assert_pv_alarm_is("KHLY2700_01:NPLCYCLES", output)

    def test_GIVEN_buffer_has_stored_reading_WHEN_queried_next_storable_location_returned(self):
          expected_location = 11
          self._lewis.backdoor_set_on_device("buffer", 10)
          self._ioc.set_simulated_value("KHLY2700_01:SIM:BUFFER_LOC", expected_location)

          self.ca.assert_that_pv_is("KHLY2700_01:BUFFER_LOC", expected_location)

    def test_GIVEN_buffer_state_set_WHEN_read_THEN_buffer_state_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["ON", "OFF"]
        for input, output in zip(sample_data, expected_state):
            self.ca.set_pv_value("KHLY2700_01:BUFFER_STATE:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:BUFFER_STATE", output)

    def test_GIVEN_time_stamp_set_WHEN_read_THEN_time_stamp_is_as_expected(self):
        sample_data = [0, 1]
        expected_state = ["ABS", "DELT"]
        for input, output in zip(sample_data, expected_state):
            self.ca.set_pv_value("KHLY2700_01:STAMP:SP", input)
            self.ca.assert_that_pv_is("KHLY2700_01:STAMP", output)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_measurement_resolution_set_WHEN_read_THEN_measurement_resolution_is_as_expected(self):
        self.ca.set_pv_value("KHLY2700_01:CHANNEL_END:SP", 110)
        self.ca.set_pv_value("KHLY2700_01:DIGIT_RANGE:SP", 6)
        self.ca.assert_that_pv_is("KHLY2700_01:DIGIT_RANGE", 6)
        self.ca.assert_that_pv_is("KHLY2700_01:CHANNEL_END", 110)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_auto_range_set_WHEN_read_THEN_auto_range_is_as_expected(self):
        self.ca.set_pv_value("KHLY2700_01:CHANNEL_END:SP", 110)
        self.ca.set_pv_value("KHLY2700_01:AUTO_RANGE:SP", 0)
        self.ca.assert_that_pv_is("KHLY2700_01:AUTO_RANGE", "ON")
        self.ca.assert_that_pv_is("KHLY2700_01:CHANNEL_END", 110)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_measurement_mode_set_to_dc_current_WHEN_read_then_measurement_mode_is_dc_current(self):
        expected_value = 26.0
        self._lewis.backdoor_set_on_device("reading", expected_value)
        expected_configuration = "DCI"
        device_mode = self._lewis.backdoor_command(["device", "get_channel_param", "1", "mode"],
                                                            returns_single_value=True)
        #self.assertEquals(device_mode, expected_configuration)
        self.ca.assert_that_pv_is("KHLY2700_01:MEAS:CURR:DC", expected_value)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_measurement_mode_set_to_dc_voltage_WHEN_read_then_measurement_mode_is_dc_voltge(self):
        expected_value = 26.0
        self._lewis.backdoor_set_on_device("reading", expected_value)
        expected_configuration = "DCV"
        self.ca.assert_that_pv_is("KHLY2700_01:MEAS:VOLT:DC", expected_value)
        device_mode = self._lewis.backdoor_command(["device", "get_channel_param", "1", "mode"],
                                                   returns_single_value=True)
        #self.assertEquals(device_mode, expected_configuration)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_data_string_set_WHEN_read_THEN_data_string_is_as_expected(self):
        self.ca.set_pv_value("KHLY2700_01:LIST_OF_ELEMENTS:SP", "READ,CHAN,TST")
        self.ca.assert_that_pv_is("KHLY2700_01:LIST_OF_ELEMENTS:SP", "READ,CHAN,TST")
        self._lewis.backdoor_set_on_device("reading", 45.0)
        self._lewis.backdoor_set_on_device("channel_number", 110)
        self._lewis.backdoor_set_on_device("time_stamp", 4)
        self.ca.set_pv_value("KHLY2700_01:LIST_OF_ELEMENTS.PROC", 1)
        self.ca.assert_that_pv_is("KHLY2700_01:LIST_OF_ELEMENTS", "45.0,110,4")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_measurement_mode_set_to_ohm_WHEN_read_then_measurement_mode_is_resistance(self):
        expected_value = 26.0
        self._lewis.backdoor_set_on_device("reading", expected_value)
        expected_configuration = "OHM"
        self.ca.assert_that_pv_is("KHLY2700_01:MEAS:FRES", expected_value)
        device_mode = self._lewis.backdoor_command(["device", "get_channel_param", "1", "mode"],
                                       returns_single_value=True)
        self.assertEquals(device_mode, expected_configuration)



