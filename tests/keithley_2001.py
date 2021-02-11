from hamcrest import assert_that, is_, greater_than, equal_to
from parameterized import parameterized
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, add_method, parameterized_list, skip_if_recsim


DEVICE_PREFIX = "KHLY2001_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2001"),
        "macros": {
            "SCAN_DELAY": 0.1
        },
        "emulator": "keithley_2001",
    },
]

TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

MAX_NUMBER_OF_CHANNELS = 10
CHANNEL_LIST = range(1, MAX_NUMBER_OF_CHANNELS + 1)


def setUp(self):
    self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
    self.ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)
    self.ca.assert_that_pv_exists("IDN")
    _connect_device(self._lewis)
    _reset_ioc(self.ca)
    _clear_errors(self.ca, self._lewis)
    _reset_channels(self.ca)
    _reset_units(self.ca)
    _reset_readings(self.ca)


setup_tests = add_method(setUp)


def _reset_ioc(ca):
    ca.set_pv_value("RESET:FLAG", 1)


def _reset_channels(ca):
    for channel in CHANNEL_LIST:
        ca.set_pv_value("CHAN:{:02d}:ACTIVE".format(channel), "INACTIVE")
        ca.assert_that_pv_is("CHAN:{:02d}:ACTIVE".format(channel), "INACTIVE")


def _reset_units(ca):
    for channel in CHANNEL_LIST:
        ca.set_pv_value("CHAN:{:02d}:UNIT:RAW.AA".format(channel), "")
        ca.assert_that_pv_is("CHAN:{:02d}:UNIT:RAW.AA".format(channel), "")


def _reset_readings(ca):
    ca.set_pv_value("READINGS", ["0"] * 20)
    ca.assert_that_pv_after_processing_is("READINGS", "".join(["0"] * 20))


def _clear_errors(ca, lewis):
    if IOCRegister.uses_rec_sim:
        ca.set_pv_value("SIM:ERROR:RAW", [str(0), "No error"])
    else:
        lewis.backdoor_run_function_on_device("clear_error")


def _setup_channel_to_test(ca, lewis, channel, value=None):
    ca.set_pv_value("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")
    ca.assert_that_pv_is("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")
    if value is not None:
        lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, value, "VDC"])


def _set_active_channel(ca, channel):
    ca.set_pv_value("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")
    ca.assert_that_pv_is("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")


def _connect_device(lewis):
    lewis.backdoor_run_function_on_device("connect")


@setup_tests
class InitTests(unittest.TestCase):

    def test_that_GIVEN_a_reset_IOC_THEN_it_is_set_up(self):
        # Given:
        self.ca.set_pv_value("RESET:FLAG", 1)

        # Then:
        self._assert_that_the_devices_status_register_is_setup()
        self._assert_that_reading_elements_are_set_to_reading_channel_and_unit()
        self._assert_that_device_trigger_mode_is_setup()

    def _assert_that_reading_elements_are_set_to_reading_channel_and_unit(self):
        self.ca.assert_that_pv_is("ELEMENTS", "READ, CHAN, UNIT")
        self.ca.assert_that_pv_after_processing_is("BUFF:EGROUP", "FULL")

    def _assert_that_device_trigger_mode_is_setup(self):
        self.ca.assert_that_pv_after_processing_is("INIT:CONT_MODE", "OFF")
        self.ca.assert_that_pv_after_processing_is("SCAN:COUNT", 1)
        self.ca.assert_that_pv_after_processing_is("SCAN:TRIG:SOURCE", "IMM")

    def _assert_that_the_devices_status_register_is_setup(self):
        self.ca.assert_that_pv_after_processing_is("STAT:MEAS", 512)
        self.ca.assert_that_pv_after_processing_is("STAT:SERVICE_REQEST", 1)

    @skip_if_recsim("Mbbi's don't work with RECSIM.")
    def test_that_GIVEN_a_fresh_IOC_THEN_the_buffer_source_is_set(self):
        # Given:
        self.ca.set_pv_value("RESET:FLAG", 1)

        # Then:
        self.ca.assert_that_pv_after_processing_is("BUFF:SOURCE", "SENS1")

    @skip_if_recsim("Lewis backdoor doesn't work in RECSIM.")
    def test_that_GIVEN_a_fresh_IOC_THEN_the_status_register_has_been_reset(self):
        # Given:
        self._lewis.backdoor_run_function_on_device(
            "set_number_of_times_status_register_has_been_reset_and_cleared_via_the_backdoor", [0])

        # When:
        self.ca.set_pv_value("RESET:FLAG", 1)

        # Then:
        number_of_times_status_register_has_been_reset_and_cleared = self._lewis.backdoor_run_function_on_device(
                "get_number_of_times_status_register_has_been_reset_and_cleared_via_the_backdoor")

        assert_that(number_of_times_status_register_has_been_reset_and_cleared, is_(equal_to(1)))


@setup_tests
class SingleShotTests(unittest.TestCase):

    def _simulate_readings(self, channel, value, unit):
        if IOCRegister.uses_rec_sim:
            simulated_reading = ["{:.7E}{}".format(value, unit), "{0:02d}INTCHAN".format(channel)]
            self.ca.set_pv_value("READINGS", simulated_reading)
        else:
            self._lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, value, unit])

    @parameterized.expand(parameterized_list([1, 5, 10]))
    def test_that_GIVEN_one_channels_set_to_active_THEN_the_voltage_value_for_that_channel_are_read(
            self, _, channel):
        # Given:
        expected_value = 9.84412
        _set_active_channel(self.ca, channel)
        self._simulate_readings(channel, expected_value, "VDC")

        # Then:
        self.ca.assert_that_pv_is("CHAN:{0:02d}:READ".format(channel), expected_value)

    @parameterized.expand(parameterized_list([1, 5, 10]))
    def test_that_GIVEN_one_channel_set_to_active_THEN_the_measurement_units_for_that_channel_are_read(
            self, _, channel):
        # Given:
        expected_value = 9.2
        _set_active_channel(self.ca, channel)
        self._simulate_readings(channel, expected_value, "VDC")

        # Then:
        expected_unit = "VDC"
        self.ca.assert_that_pv_is("CHAN:{0:02d}:UNIT".format(channel), expected_unit)

    @parameterized.expand(parameterized_list([1, 5, 10]))
    def test_that_GIVEN_one_channel_set_to_active_THEN_the_measurement_units_for_that_channel_are_read(
            self, _, channel):
        # Given:
        expected_value = 9.2
        _set_active_channel(self.ca, channel)
        self._simulate_readings(channel, expected_value, "mVDC")

        # Then:
        expected_unit = "mVDC"
        self.ca.assert_that_pv_is("CHAN:{0:02d}:UNIT".format(channel), expected_unit)


@setup_tests
class ScanningSetupTests(unittest.TestCase):

    def test_that_GIVEN_two_active_channels_WHEN_scanning_on_two_channels_THEN_the_buffer_size_is_set_to_two(self):
        # Given:
        channels = (1, 2)
        for channel in channels:
            self.ca.set_pv_value("CHAN:{:02d}:ACTIVE".format(channel), 1)

        # Then:
        self.ca.assert_that_pv_after_processing_is("BUFF:SIZE", len(channels))

    def test_that_GIVEN_two_active_channels_WHEN_scanning_on_two_channels_THEN_the_measurement_count_is_set_to_two(
            self):
        # Given:
        channels = (1, 2)
        for channel in channels:
            self.ca.set_pv_value("CHAN:{:02d}:ACTIVE".format(channel), 1)

        # Then:
        self.ca.assert_that_pv_after_processing_is("SCAN:MEAS:COUNT", len(channels))

    @skip_if_recsim("Can't use lewis with RECSIM")
    def test_that_GIVEN_two_active_channels_THEN_the_buffer_is_cleared(self):
        # Given:
        channels = (1, 2)
        for channel in channels:
            self.ca.set_pv_value("CHAN:{:02d}:ACTIVE".format(channel), 1)

        # Then:
        number_of_times_buffer_has_been_cleared = self._lewis.backdoor_run_function_on_device(
            "get_number_of_times_buffer_has_been_cleared_via_the_backdoor")
        assert_that(number_of_times_buffer_has_been_cleared, is_(greater_than(1)))

    @parameterized.expand(parameterized_list([
        [1, 2], [1, 2, 3, 4], [6, 7, 8, 9], [1, 5, 10]
        ]))
    def test_that_GIVEN_IOC_with_active_channels_THEN_the_IOC_creates_the_correct_string_to_send_to_the_device(
            self, _, active_channels):
        # Given:
        for channel in active_channels:
            self.ca.set_pv_value("CHAN:{:02d}:ACTIVE".format(channel), 1)
            self.ca.assert_that_pv_is("CHAN:{:02d}:ACTIVE".format(channel), "ACTIVE")

        # Then:
        expected_channel_string = ",".join([str(i) for i in active_channels])
        self.ca.assert_that_pv_is("SCAN:CHAN:SP", expected_channel_string)


@setup_tests
class ScanningTests(unittest.TestCase):

    def _simulate_readings(self, values, channels, unit):
        if IOCRegister.uses_rec_sim:
            simulated_readings = []
            for value, channel in zip(values, channels):
                simulated_readings.extend(["{:.7E}{}".format(value, unit), "{0:02d}INTCHAN".format(channel)])
            self.ca.set_pv_value("READINGS", simulated_readings)
        else:
            for value, channel in zip(values, channels):
                self._lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, value, unit])

    @parameterized.expand(parameterized_list([
        [1, 2], [1, 2, 3, 4], [1, 5, 10]
    ]))
    def test_that_GIVEN_two_or_more_active_channels_THEN_the_readings_values_are_read_into_CHAN_READ_PV(
            self, _, channels):
        # Given:
        expected_values = [9.2] * len(channels)
        [_set_active_channel(self.ca, channel) for channel in channels]
        self._simulate_readings(expected_values, channels, "VDC")

        # Then:
        for expected_value, channel in zip(expected_values, channels):
            self.ca.assert_that_pv_is("CHAN:{0:02d}:READ".format(channel), expected_value)

    @parameterized.expand(parameterized_list([
        [1, 2], [1, 2, 3, 4], [1, 5, 10]
    ]))
    def test_that_GIVEN_two_or_more_active_channels_THEN_VDC_is_parsed_into_the_unit_records(
            self, _, channels):
        # Given:
        expected_values = [9.2] * len(channels)
        [_set_active_channel(self.ca, channel) for channel in channels]
        self._simulate_readings(expected_values, channels, "VDC")

        # Then:
        expected_unit = "VDC"
        for expected_value, channel in zip(expected_values, channels):
            self.ca.assert_that_pv_is("CHAN:{0:02d}:UNIT".format(channel), expected_unit)

    @parameterized.expand(parameterized_list([
        [1, 2], [1, 2, 3, 4], [1, 5, 10]
    ]))
    def test_that_GIVEN_two_or_more_active_channels_THEN_mVDC_is_parsed_into_the_unit_records(
            self, _, channels):
        # Given:
        expected_values = [9.2] * len(channels)
        [_set_active_channel(self.ca, channel) for channel in channels]
        self._simulate_readings(expected_values, channels, "mVDC")

        # Then:
        expected_unit = "mVDC"
        for expected_value, channel in zip(expected_values, channels):
            self.ca.assert_that_pv_is("CHAN:{0:02d}:UNIT".format(channel), expected_unit)


@setup_tests
class ErrorTests(unittest.TestCase):

    def _simulate_error(self, error_code, error_message):
        if IOCRegister.uses_rec_sim:
            self.ca.set_pv_value("SIM:ERROR:RAW", [str(error_code), error_message])
        else:
            self._lewis.backdoor_run_function_on_device("set_error_via_the_backdoor",
                                                        [error_code, error_message])

    def test_that_GIVEN_a_device_not_scanning_on_any_channels_with_no_error_THEN_the_IOC_reads_that_there_are_no_errors(
            self):
        expected_error_code = 0
        expected_error_message = "No error"
        # Then:
        self.ca.assert_that_pv_is("ERROR:RAW", "".join([str(expected_error_code), expected_error_message]))

    def test_that_GIVEN_a_device_not_scanning_on_any_channels_with_an_error_THEN_the_IOC_reads_that_there_is_an_error(
            self):
        # Given:
        expected_error_code = -113
        expected_error_message = "Undefined header"
        self._simulate_error(expected_error_code, expected_error_message)

        # Then:
        self.ca.assert_that_pv_is("ERROR:RAW", "".join([str(expected_error_code), expected_error_message]))

    def test_that_GIVEN_a_device_scanning_on_one_channels_with_an_error_THEN_the_IOC_reads_that_there_is_an_error(
            self):
        # Given:
        _set_active_channel(self.ca, 3)
        expected_error_code = -113
        expected_error_message = "Undefined header"
        self._simulate_error(expected_error_code, expected_error_message)

        # Then:
        self.ca.assert_that_pv_is("ERROR:RAW", "".join([str(expected_error_code), expected_error_message]))

    def test_that_GIVEN_a_device_scanning_on_two_channels_with_an_error_THEN_the_IOC_reads_that_there_is_an_error(
            self):
        # Given:
        _set_active_channel(self.ca, 3)
        _set_active_channel(self.ca, 5)
        expected_error_code = -113
        expected_error_message = "Undefined header"
        self._simulate_error(expected_error_code, expected_error_message)

        # Then:
        self.ca.assert_that_pv_is("ERROR:RAW", "".join([str(expected_error_code), expected_error_message]))

    def test_that_GIVEN_a_device_not_scanning_on_any_channels_with_an_error_THEN_the_error_code_and_error_message_are_separatated(
            self):
        # Given:
        expected_error_code = -113
        expected_error_message = "Undefined header"
        self._simulate_error(expected_error_code, expected_error_message)

        # Then:
        self.ca.assert_that_pv_is("ERROR:MSG", expected_error_message)
        self.ca.assert_that_pv_is("ERROR:CODE", expected_error_code)


    def test_that_GIVEN_a_device_not_scanning_on_any_channels_with_an_error_THEN_the_error_code_PV_goes_into_alarm(
            self):
        # Given:
        expected_error_code = -113
        expected_error_message = "Undefined header"
        self._simulate_error(expected_error_code, expected_error_message)

        # Then:
        self.ca.assert_that_pv_alarm_is("ERROR:CODE", self.ca.Alarms.MAJOR)


@setup_tests
class DisconnectedTests(unittest.TestCase):

    def _disconnect_device(self):
        self._lewis.backdoor_run_function_on_device("disconnect")

    @skip_if_recsim("Can't simulate a disconnected device using RECSIM")
    def test_that_GIVEN_a_disconnected_device_set_to_scan_on_one_channel_WHEN_it_tries_to_scan_THEN_the_channel_read_pv_goes_into_alarm(
            self):
        # Given:
        self._disconnect_device()
        _set_active_channel(self.ca, 1)
        self.ca.assert_that_pv_alarm_is("ERROR:RAW", self.ca.Alarms.INVALID)

        # When/Then:
        self.ca.assert_that_pv_alarm_is("CHAN:01:READ", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is("CHAN:01:UNIT", self.ca.Alarms.INVALID)

    @skip_if_recsim("Can't simulate a disconnected device using RECSIM")
    def test_that_GIVEN_a_disconnected_device_set_to_scan_on_three_channels_WHEN_it_tries_to_scan_THEN_all_channel_read_pvs_are_in_alarm(
            self):
        # Given:
        self._disconnect_device()
        map(_set_active_channel, [self.ca] * 3, range(1, 3 + 1))
        self.ca.assert_that_pv_alarm_is("ERROR:RAW", self.ca.Alarms.INVALID)

        # When/Then:
        map(self.ca.assert_that_pv_alarm_is, ["CHAN:0{}:UNIT".format(i) for i in range(1, 3 + 1)],
            [self.ca.Alarms.INVALID] * 3)
        map(self.ca.assert_that_pv_alarm_is, ["CHAN:0{}:READ".format(i) for i in range(1, 3 + 1)],
            [self.ca.Alarms.INVALID] * 3)

    @skip_if_recsim("Can't simulate a disconnected device using RECSIM")
    def test_that_GIVEN_a_device_set_to_scan_on_one_channels_WHEN_disconnected_THEN_channel_read_pv_is_in_alarm(
            self):
        # Given:
        channel = 1
        value = 9
        _set_active_channel(self.ca, channel)

        self._lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, value, "VDC"])
        self.ca.assert_that_pv_is("CHAN:0{}:READ".format(channel), value)

        # When:
        self._disconnect_device()
        self.ca.assert_that_pv_alarm_is("ERROR:RAW", self.ca.Alarms.INVALID)

        # When/Then:
        self.ca.assert_that_pv_alarm_is("CHAN:01:READ", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is("CHAN:01:UNIT", self.ca.Alarms.INVALID)


@setup_tests
class IOCResetTests(unittest.TestCase):

    @skip_if_recsim("Can't replicate resetting the device in RECSIM")
    def test_that_GIVEN_a_device_WHEN_reset_THEN_the_IOC_has_been_reinitalized(
            self):
        # Given:
        previous_number_of_times_the_device_has_been_reset = self._lewis.backdoor_run_function_on_device(
            "get_how_many_times_ioc_has_been_reset_via_the_backdoor")

        # When:
        self.ca.set_pv_value("RESET:FLAG", 1)

        # Then:
        result = self._lewis.backdoor_run_function_on_device("get_how_many_times_ioc_has_been_reset_via_the_backdoor")
        assert_that(result, is_(equal_to(previous_number_of_times_the_device_has_been_reset + 1)))
