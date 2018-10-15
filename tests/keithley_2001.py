from hamcrest import assert_that, is_, greater_than, greater_than_or_equal_to
from parameterized import parameterized
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, add_method, parameterized_list


DEVICE_PREFIX = "KHLY2001_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2001"),
        "macros": {},
        "emulator": "keithley_2001",
    },
]

# Only one test does not uses the lewis backdoor feature.
# Therefore these tests only run in DEVSIM.
TEST_MODES = [TestModes.DEVSIM]

CHANNEL_LIST = range(1, 11)


def setUp(self):
    self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
    self.ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)
    self.ca.assert_that_pv_exists("IDN")
    _reset_channels(self.ca)
    _reset_units(self.ca)
    _reset_readings(self.ca)


setup_tests = add_method(setUp)


def _reset_channels(ca):
    for channel in CHANNEL_LIST:
        ca.set_pv_value("CHAN:{:02d}:ACTIVE".format(channel), "INACTIVE")
        ca.assert_that_pv_is("CHAN:{:02d}:ACTIVE".format(channel), "INACTIVE")


def _reset_units(ca):
    for channel in CHANNEL_LIST:
        ca.set_pv_value("CHAN:{:02d}:UNIT".format(channel), "")
        ca.assert_that_pv_is("CHAN:{:02d}:UNIT".format(channel), "")


def _reset_readings(ca):
    ca.set_pv_value("READINGS", ["0"] * 20)
    ca.assert_that_pv_is("READINGS", "".join(["0"] * 20))


def _setup_channel_to_test(ca, lewis, channel, value=None):
    ca.set_pv_value("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")
    ca.assert_that_pv_is("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")
    if value is not None:
        lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, value])


@setup_tests
class InitTests(unittest.TestCase):

    def test_that_GIVEN_a_fresh_IOC_THEN_it_is_set_up(self):
        # Then:
        self._lewis.assert_that_emulator_value_is_greater_than("number_of_times_device_has_been_reset", 1)
        self.__assert_that_the_devices_status_register_is_setup()
        self._assert_that_the_buffer_is_setup()
        self._assert_that_device_trigger_mode_is_setup()
        self.ca.assert_that_pv_is("ELEMENTS", "READ, CHAN, UNIT")

    def _assert_that_device_trigger_mode_is_setup(self):
        self.ca.assert_that_pv_after_processing_is("INIT:CONT_MODE", "OFF")
        self.ca.assert_that_pv_after_processing_is("SCAN:COUNT", 1)
        self.ca.assert_that_pv_after_processing_is("SCAN:TRIG:SOURCE", "IMM")

    def __assert_that_the_devices_status_register_is_setup(self):
        number_of_times_status_register_has_been_reset_and_cleared = int(self._lewis.backdoor_run_function_on_device(
            "get_number_of_times_status_register_has_been_reset_and_cleared_via_the_backdoor")[0])

        assert_that(number_of_times_status_register_has_been_reset_and_cleared, is_(greater_than_or_equal_to(1)))
        self.ca.assert_that_pv_after_processing_is("STAT:MEAS", 512)
        self.ca.assert_that_pv_after_processing_is("STAT:SERVICE_REQEST", 1)

    def _assert_that_the_buffer_is_setup(self):
        number_of_times_buffer_has_been_cleared = int(self._lewis.backdoor_run_function_on_device(
            "get_number_of_times_buffer_has_been_cleared_via_the_backdoor")[0])

        self.ca.assert_that_pv_after_processing_is("BUFF:SOURCE", "SENS1")
        self.ca.assert_that_pv_after_processing_is("BUFF:EGROUP", "FULL")
        assert_that(number_of_times_buffer_has_been_cleared, is_(greater_than_or_equal_to(1)))


@setup_tests
class ReadingTests(unittest.TestCase):

    def _setup_channel_to_test(self, channel, value=None):
        self.ca.set_pv_value("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")
        self.ca.assert_that_pv_is("CHAN:{0:02d}:ACTIVE".format(channel), "ACTIVE")
        if value is not None:
            self._lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, value])

    @parameterized.expand(parameterized_list(range(1, 11)))
    def test_that_GIVEN_one_channels_set_to_active_THEN_the_voltage_value_for_that_channel_are_read(
            self, _, channel):
        # Given:
        expected_value = 9.84412
        _setup_channel_to_test(self.ca, self._lewis, channel, expected_value)

        # Then:
        self.ca.assert_that_pv_is("CHAN:{0:02d}:READ".format(channel), expected_value)

    @parameterized.expand(parameterized_list(range(1, 11)))
    def test_that_GIVEN_one_channel_set_to_active_THEN_the_measurement_units_for_that_channel_are_read(
            self, _, channel):
        # Given:
        expected_value = 9.2
        _setup_channel_to_test(self.ca, self._lewis, channel, expected_value)

        # Then:
        expected_unit = "VDC"
        self.ca.assert_that_pv_is("CHAN:{0:02d}:UNIT".format(channel), expected_unit)

    def test_that_GIVEN_two_active_channels_THEN_the_IOC_is_setup_to_scan_on_those_channels(self):
        # Given:
        channels = (1, 2)
        for channel in channels:
            self.ca.set_pv_value("CHAN:{:02d}:ACTIVE".format(channel), 1)

        # Then:
        self.ca.assert_that_pv_after_processing_is("BUFF:SIZE", len(channels))
        self.ca.assert_that_pv_after_processing_is("SCAN:MEAS:COUNT", len(channels))
        self.ca.assert_that_pv_is("BUFF:MODE", "NEXT")
        number_of_times_buffer_has_been_cleared = int(self._lewis.backdoor_run_function_on_device(
            "get_number_of_times_buffer_has_been_cleared_via_the_backdoor")[0])
        assert_that(number_of_times_buffer_has_been_cleared, is_(greater_than(1)))

    def test_that_GIVEN_five_active_channels_THEN_the_IOC_sets_the_device_to_scan_on_those__channels(self):
        # Given:
        channels = (1, 2, 3, 8, 9)
        map(self._setup_channel_to_test, channels)

        # Then:
        expected_string = "1,2,3,8,9"
        self.ca.process_pv("SCAN:CHAN")
        self.ca.assert_that_pv_is("SCAN:CHAN", expected_string)

    def test_that_GIVEN_only_channels_2_and_5_active_THEN_the_readings_are_read_into_channels_2_and_5(
            self):
        # Given:
        active_channels = (2, 5)
        expected_values = [9.2] * len(active_channels)
        map(self._setup_channel_to_test, active_channels, expected_values)

        # Then:
        for expected_value, channel in zip(expected_values, active_channels):
            self.ca.assert_that_pv_is("CHAN:{0:02d}:READ".format(channel), expected_value)

    def test_that_GIVEN_only_channels_2_and_5_active_THEN_the_units_are_read_into_channels_2_and_5_units(
            self):
        # Given:
        active_channels = (2, 5)
        expected_values = [9.2] * len(active_channels)
        map(self._setup_channel_to_test, active_channels, expected_values)

        # Then:
        expected_unit = "VDC"
        for expected_value, channel in zip(expected_values, active_channels):
            self.ca.assert_that_pv_is("CHAN:{0:02d}:UNIT".format(channel), expected_unit)
