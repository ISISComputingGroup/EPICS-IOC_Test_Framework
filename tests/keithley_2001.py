import ast
import itertools
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

TEST_MODES = [TestModes.DEVSIM] # TestModes.RECSIM]

CHANNEL_LIST = [1, 2, 3, 4, 6, 7, 8, 9]


def setUp(self):
    self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
    self.ca = ChannelAccess(default_timeout=20, device_prefix=DEVICE_PREFIX)
    self.ca.assert_that_pv_exists("IDN")


setup_tests = add_method(setUp)


@setup_tests
class BasicCommands(unittest.TestCase):

    def test_that_GIVEN_a_fresh_IOC_THEN_the_IDN_is_correct(self):
        expected_idn = "MODEL 2001,4301578,B17  /A02  "
        self.ca.assert_that_pv_is("IDN", expected_idn)



@setup_tests
class ScanStartUpTests(unittest.TestCase):

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_initialization_mode_is_set_to_continuous(self):
        # Then:
        initialization_mode = list(self._lewis.backdoor_get_from_device("initialization_mode"))
        self._lewis.assert_that_emulator_value_is(initialization_mode, "continuous")

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_scan_rate_is_set_to_half_a_second(self):
        # Then:
        expected_scan_rate = 0.5
        scan_rate = float(self._lewis.backdoor_get_from_device("scan_rate"))
        self._lewis.assert_that_emulator_value_is(scan_rate, expected_scan_rate)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_read_back_elements_are_reading_and_unit(self):
        # Then:
        expected_read_back_elements = "READ, UNIT"
        self.ca.assert_that_pv_is("ELEMENTS", expected_read_back_elements)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_the_device_is_scanning(self):
        # Then:
        expected_scan_status = True
        scan_status = bool(self._lewis.backdoor_get_from_device("scan_status"))
        self._lewis.assert_that_emulator_value_is("scan_status", expected_scan_status)


@setup_tests
class BufferStartUpTests(unittest.TestCase):

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_is_cleared_before_starting(self):
        # Then:
        buffer_cleared = self._lewis.backdoor_get_from_device("buffer_cleared")
        self._lewis.assert_that_emulator_value_is(buffer_cleared, True)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_reads_raw_values(self):
        # Then:
        expected_buffer_source = "SENS"
        self.ca.assert_that_pv_is("BUFF:SOURCE", expected_buffer_source)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_control_mode_is_set_to_always(self):
        # Then:
        expected_buffer_control_mode = "ALWAYS"
        self.ca.assert_that_pv_is("BUFF:CNTRL:STATUS", expected_buffer_control_mode)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_size_is_1000(self):
        # Then:
        expected_buffer_size = 1000
        self.ca.assert_that_pv_is("BUFF:SIZE", expected_buffer_size)


@setup_tests
class ChannelSetupTests(unittest.TestCase):

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_no_channels_set_to_active_THEN_no_channels_are_set_to_scan(self):
        # Then:
        expected_channels = "(@)"
        self.ca.assert_that_pv_is("SCAN:CHAN:STATUS", expected_channels)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_one_channels_set_to_active_THEN_only_the_active_channels_are_set_to_scan(self):
        # Given:
        self.ca.set_pv_value("CHAN:01:ACTIVE", 1)
        self.ca.process_pv("startup")

        # Then:
        expected_channels = "1"
        self.ca.assert_that_pv_is("SCAN:CHAN:STATUS", expected_channels)

    @skip_if_recsim("Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_first_four_channels_set_to_active_THEN_only_the_active_channels_are_set_to_scan(
            self):
        # Given:
        expected_channels = [1, 2, 3, 4]

        for i in expected_channels:
            self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(i), 1)
        self.ca.process_pv("startup")

        # Then:
        expected_channels = "1,2,3,4"
        self.ca.assert_that_pv_is("SCAN:CHAN:STATUS", expected_channels)


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


@setup_tests
class ChannelReadingTests(unittest.TestCase):
    TEST_VOLTAGES = [0, -2.3586, +1.05e9, 589, 2, 2.8654852]

    @parameterized.expand(parameterized_list(itertools.product(TEST_VOLTAGES, CHANNEL_LIST)))
    def GIVEN_a_fresh_IOC_THEN_the_channels_are_reading_the_correct_values_from_the_buffer(self, _, voltage, channel):
        # Then:
        self._lewis.backdoor_set_on_device("CHAN:0{}".format(channel), voltage)
        self.ca.assert_that_pv_is("CHAN:0{}".format(channel), voltage)
