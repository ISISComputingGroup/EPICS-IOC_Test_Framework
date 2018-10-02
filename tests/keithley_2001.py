import ast
import itertools
from hamcrest import assert_that, is_
from parameterized import parameterized
import unittest
import time

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, add_method, parameterized_list


DEVICE_PREFIX = "KHLY2001_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KHLY2001"),
        "macros": {},
        "emulator": "keithley_2001",
    },
]

TEST_MODES = [TestModes.DEVSIM]#, TestModes.RECSIM]

CHANNEL_LIST = [1, 2, 3, 4, 6, 7, 8, 9]


def _reset_channels(ca):
    for channel in CHANNEL_LIST:
        ca.set_pv_value("CHAN:0{}:ACTIVE".format(channel), 0)


def setUp(self):
    self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
    self.ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)
    self.ca.assert_that_pv_exists("IDN")
    _reset_channels(self.ca)


setup_tests = add_method(setUp)


@setup_tests
class InitTests(unittest.TestCase):

    def test_that_GIVEN_a_fresh_IOC_THEN_the_IDN_is_correct(self):
        expected_idn = "MODEL 2001,4301578,B17  /A02  "
        self.ca.assert_that_pv_is("IDN", expected_idn)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_THEN_the_device_is_reset(self):
        self._lewis.assert_that_emulator_value_is("number_of_times_reset", "1")

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_THEN_the_status_registers_are_reset_and_cleared(self):
        # Then:
        number_of_times_status_register_has_been_reset_and_cleared = self._lewis.backdoor_run_function_on_device(
            "get_number_of_times_status_register_has_been_reset_and_cleared_via_the_backdoor")[0]
        assert_that(number_of_times_status_register_has_been_reset_and_cleared, is_("1"))

    def test_that_GIVEN_a_fresh_IOC_THEN_the_read_back_elements_are_reading_and_unit(self):
        # Then:
        expected_read_back_elements = "READ, UNIT"
        self.ca.assert_that_pv_is("ELEMENTS", expected_read_back_elements)

    def test_that_GIVEN_a_fresh_IOC_THEN_the_scanning_continuous_mode_is_ON(self):
        # Then:
        expected_initialization_mode = "OFF"
        self.ca.process_pv("INIT:CONT_MODE")
        self.ca.assert_that_pv_is("INIT:CONT_MODE", expected_initialization_mode)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_THEN_the_buffer_is_cleared_before_starting(self):
        # Then:
        number_of_times_buffer_has_been_cleared = self._lewis.backdoor_run_function_on_device(
            "get_number_of_times_buffer_has_been_cleared_via_the_backdoor")[0]
        assert_that(number_of_times_buffer_has_been_cleared, is_("1"))

    @skip_if_recsim("Uses mbbi & mbbo records which do not play well with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_THEN_the_buffer_reads_raw_values(self):
        # Then:
        expected_buffer_source = "SENS1"
        self.ca.process_pv("BUFF:SOURCE")
        self.ca.assert_that_pv_is("BUFF:SOURCE", expected_buffer_source)

    def test_that_GIVEN_a_fresh_IOC_THEN_the_buffer_element_group_is_full(self):
        # Then:
        expected_buffer_element_group = "FULL"
        self.ca.process_pv("BUFF:EGROUP")
        self.ca.assert_that_pv_is("BUFF:EGROUP", expected_buffer_element_group)

    @skip_if_recsim("Cannot simulate records of different types")
    def test_that_GIVEN_a_fresh_ioc_THEN_the_buffer_full_status_bit_will_be_set_when_the_buffer_is_full(self):
        # Then:
        self.ca.process_pv("STAT:MEAS")
        self.ca.assert_that_pv_is("STAT:MEAS", 512)

    @skip_if_recsim("Cannot simulate records of different types")
    def test_that_GIVEN_a_fresh_ioc_THEN_the_measurement_summary_status_bit_is_enabled(self):
        # Then:
        self.ca.process_pv("STAT:SERVICE_REQEST")
        self.ca.assert_that_pv_is("STAT:SERVICE_REQEST", 1)

    @skip_if_recsim("Cannot simulate records of different types")
    def test_that_GIVEN_a_fresh_ioc_THEN_scan_layer_is_set_to_scan_once(self):
        # Then:
        self.ca.process_pv("SCAN:COUNT")
        self.ca.assert_that_pv_is("SCAN:COUNT", 1)

    @skip_if_recsim("Cannot simulate records of different types")
    def test_that_GIVEN_a_fresh_ioc_THEN_scan_trigger_is_set_to_immediate(self):
        # Then:
        self.ca.process_pv("SCAN:TRIG:SOURCE")
        self.ca.assert_that_pv_is("SCAN:TRIG:SOURCE", "IMM")


@setup_tests
class ChannelSetupTests(unittest.TestCase):

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_with_no_channels_set_to_active_THEN_the_IOC_is_in_IDLE_scan_mode(self):
        # Then:
        expected_mode = "IDLE"
        self.ca.assert_that_pv_is("READ:MODE", expected_mode)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_with_one_channels_set_to_active_THEN_the_IOC_is_in_SINGLE_scan_mode(self):
        # Given:
        self.ca.set_pv_value("CHAN:01:ACTIVE", 1)

        # Then:
        expected_mode = "SINGLE"
        self.ca.assert_that_pv_is("READ:MODE", expected_mode)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_with_first_four_channels_set_to_active_THEN_the_IOC_is_in_MULTI_scan_mode(self):
        # Given:
        expected_channels = [1, 2, 3]

        for i in expected_channels:
            self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(i), 1)

        # Then:
        expected_mode = "MULTI"
        self.ca.assert_that_pv_is("READ:MODE", expected_mode)

    @parameterized.expand(parameterized_list(CHANNEL_LIST))
    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_with_one_channels_set_to_active_THEN_the_IOC_scans_on_that_channel(
            self, _, channel):
        # Given:
        self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(channel), 1)

        # Then:
        expected_channel = "{}".format(channel)
        self.ca.assert_that_pv_is("READ:SINGLE:SP", expected_channel)


@setup_tests
class SingleChannelReadingTests(unittest.TestCase):

    @parameterized.expand(parameterized_list(CHANNEL_LIST))
    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_with_one_channels_set_to_active_THEN_the_IOC_reads_the_correct_value(
            self, _, channel):
        # Given:
        expected_value = 9.84412
        channel_pv_root = "CHAN:0{}".format(channel)
        self.ca.set_pv_value("{}:ACTIVE".format(channel_pv_root), 1)
        self._lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, expected_value])

        # Then:
        self.ca.assert_that_pv_is("{}:READ".format(channel_pv_root), expected_value)

    @parameterized.expand(parameterized_list(CHANNEL_LIST))
    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def test_that_GIVEN_a_fresh_IOC_with_one_channels_set_to_active_THEN_the_IOC_reads_the_correct_units(
            self, _, channel):
        # Given:
        expected_value = 9.2
        channel_pv_root = "CHAN:0{}".format(channel)
        self.ca.set_pv_value("{}:ACTIVE".format(channel_pv_root), 1)
        self._lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, expected_value])

        # Then:
        expected_unit = "VDC"
        self.ca.assert_that_pv_is("{}:UNIT".format(channel_pv_root), expected_unit)


@setup_tests
class BufferSetupTests(unittest.TestCase):

    def test_that_GIVEN_two_active_channels_THEN_the_IOC_sets_the_buffer_size_to_2(self):
        channels = (1, 2)

        # Given:
        for channel in channels:
            self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(channel), 1)

        # Then:
        self.ca.process_pv("BUFF:SIZE")
        self.ca.assert_that_pv_is("BUFF:SIZE", len(channels))

    def test_that_GIVEN_two_active_channels_THEN_the_measurement_scan_count_is_set_to_2(self):
        channels = (1, 2)

        # Given:
        for channel in channels:
            self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(channel), 1)

        # Then:
        self.ca.process_pv("SCAN:MEAS:COUNT")
        self.ca.assert_that_pv_is("SCAN:MEAS:COUNT", len(channels))


@setup_tests
class MultiChannelReadingTests(unittest.TestCase):

    def test_that_GIVEN_a_fresh_IOC_with_two_channels_set_to_active_THEN_the_IOC_reads_the_right_values_in_the_channels_read_pvs(
            self):
        channels = (1, 2)

        # Given:
        expected_values = (9.2, 8.3)
        for channel, expected_value in zip(channels, expected_values):
            self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(channel), 1)
            self._lewis.backdoor_run_function_on_device("set_channel_value_via_the_backdoor", [channel, expected_value])

        # Then:
        for channel, expected_value in zip(channels, expected_values):
            self.ca.assert_that_pv_is("CHAN:0{}:READ".format(channel), expected_value)


@setup_tests
class MeasurementSetupTests(unittest.TestCase):

    @parameterized.expand(parameterized_list(CHANNEL_LIST))
    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_measurement_mode_for_each_channel_is_VOLT_DC(self):
        # Then:
        expected_measurement_mode = "VOLT:DC"
        self.ca.assert_that_pv_is("CHAN:0{}:MEAS", expected_measurement_mode)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_precision_of_VOLT_DC_measurement_mode_is_5(self):
        # Then:
        precision = 5
        self.ca.assert_that_pv_is("VOLT:DC:PREC", precision)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_VOLT_DC_autorange_is_ON(self):
        # Then:
        self.ca.assert_that_pv_is("VOLT:DC:RANGE:AUTO", "ON")

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_auto_aperture_of_volt_dc_is_on(self):
        # Then:
        self.ca.assert_that_pv_is("VOLT:DC:APER:AUTO", "ON")


@setup_tests
class ErrorTests(unittest.TestCase):

    def GIVEN_a_set_up_device_THEN_their_are_no_errors(self):
        # Then:
        expected_error_status = "No error"
        self.ca.assert_that_pv_is("ERROR", expected_error_status)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_device_with_errors_WHEN_clearing_the_errors_THEN_the(self):
        # Given:
        error_status_to_be_set = "ERORR CODE 14 - An error"
        self._lewis.backdoor_set_on_device("error", error_status_to_be_set)
        time.sleep(1)
        self.ca.assert_that_pv_is("ERROR", error_status_to_be_set)

        # When:
        self.ca.process_pv("ERROR:CLEAR")

        # Then:
        expected_cleared_error_status = "No error"
        self.ca.assert_that_pv_is("ERROR", expected_cleared_error_status)
