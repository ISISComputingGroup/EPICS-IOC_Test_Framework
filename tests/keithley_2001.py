import unittest
import ast

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, add_method


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


def setUp(self):
    self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
    self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
    self.ca.assert_that_pv_exists("IDN")
    # Given:
    self.ca.process_pv("startup")


setup_tests = add_method(setUp)


@setup_tests
class ScanStartUpTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("keithley_2001", DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("IDN")
        # Given:
        self.ca.process_pv("startup")

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_initialization_mode_is_set_to_continuous(self):
        # Then:
        initialization_mode = list(self._lewis.backdoor_get_from_device("initialization_mode"))
        self._lewis.assert_that_emulator_value_is(initialization_mode, "continuous")

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_scan_rate_is_set_to_half_a_second(self):
        # Then:
        expected_scan_rate = 0.5
        scan_rate = float(self._lewis.backdoor_get_from_device("scan_rate"))
        self._lewis.assert_that_emulator_value_is(scan_rate, expected_scan_rate)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_read_back_elements_are_reading_and_unit(self):
        # Then:
        expected_read_back_elements = {"READ", "UNIT"}
        read_back_elements = set(ast.literal_eval(self._lewis.backdoor_get_from_device("read_back_elements")))
        self._lewis.assert_that_emulator_value_is(read_back_elements, expected_read_back_elements)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_the_device_is_set_to_scan(self):
        # Then:
        expected_scan_status = "SCANNING"
        scan_status = float(self._lewis.backdoor_get_from_device("scan_status"))
        self._lewis.assert_that_emulator_value_is(scan_status, expected_scan_status)


@setup_tests
class BufferStartUpTests(unittest.TestCase):

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_is_cleared_before_starting(self):
        # Then:
        buffer_cleared = self._lewis.backdoor_get_from_device("buffer_cleared")
        self._lewis.assert_that_emulator_value_is(buffer_cleared, False)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_buffer_autoclear_is_turned_on(self):
        # Then:
        voltage_precision = self._lewis.backdoor_get_from_device("buffer_autoclear")
        self._lewis.assert_that_emulator_value_is(voltage_precision, True)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_reads_raw_values(self):
        # Then:
        buffer_source = self._lewis.backdoor_get_from_device("buffer_source")
        self._lewis.assert_that_emulator_value_is(buffer_source, "RAW")

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_control_mode_is_set_to_always(self):
        # Then:
        buffer_control_mode = self._lewis.backdoor_get_from_device("buffer_control_mode")
        self._lewis.assert_that_emulator_value_is(buffer_control_mode, "ALWAYS")

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_buffer_size_is_1000(self):
        # Then:
        expected_buffer_size = 1000
        buffer_size = self._lewis.backdoor_get_from_device("buffer_size")
        self._lewis.assert_that_emulator_value_is(buffer_size, expected_buffer_size)


@setup_tests
class ChannelSetupTests(unittest.TestCase):

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_no_channels_set_to_active_THEN_no_channels_are_set_to_scan(self):
        # Then:
        expected_channels = [1]
        channels_to_scan = list(self._lewis.backdoor_get_from_device("channels_to_scan"))
        self._lewis.assert_that_emulator_value_is(channels_to_scan, expected_channels)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_one_channels_set_to_active_THEN_only_the_active_channels_are_set_to_scan(self):
        # Given:
        self.ca.set_pv_value("CHAN:01:ACTIVE", 1)
        self.ca.process_pv("startup")

        # Then:
        expected_channels = [1]
        channels_to_scan = list(self._lewis.backdoor_get_from_device("channels_to_scan"))
        self._lewis.assert_that_emulator_value_is(channels_to_scan, expected_channels)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_with_first_four_channels_set_to_active_THEN_only_the_active_channels_are_set_to_scan(
            self):
        # Given:
        expected_channels = [1, 2, 3, 4]

        for i in expected_channels:
            self.ca.set_pv_value("CHAN:0{}:ACTIVE".format(i), 1)
        self.ca.process_pv("startup")

        # Then:
        channels_to_scan = list(self._lewis.backdoor_get_from_device("channels_to_scan"))
        self._lewis.assert_that_emulator_value_is(channels_to_scan, expected_channels)


@setup_tests
class MeasurementSetupTests(unittest.TestCase):

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_measurement_mode_for_each_channel_is_VDC(self):
        # Then:
        expected_measurement_modes = {
            "CHAN:01": "V:DC",
            "CHAN:02": "V:DC",
            "CHAN:03": "V:DC",
            "CHAN:04": "V:DC",
            "CHAN:06": "V:DC",
            "CHAN:07": "V:DC",
            "CHAN:08": "V:DC",
            "CHAN:09": "V:DC"
        }
        measurement_modes = ast.literal_eval(self._lewis.backdoor_get_from_device("scan_rate"))
        self._lewis.assert_that_emulator_value_is(measurement_modes, expected_measurement_modes)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_precision_of_VOLT_DC_measurement_mode_is_5(self):
        # Then:
        precision = 5
        voltage_precision = self._lewis.backdoor_get_from_device("voltage_precision")
        self._lewis.assert_that_emulator_value_is(voltage_precision, precision)

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_VOLT_DC_autorange_is_ON(self):
        # Then:
        voltage_precision = self._lewis.backdoor_get_from_device("voltage_autorange")
        self._lewis.assert_that_emulator_value_is(voltage_precision, "ON")

    @skip_if_recsim(" Cannot use Lewis backdoor used with RECSIM")
    def GIVEN_a_fresh_IOC_THEN_the_auto_aperture_of_volt_dc_is_on(self):
        # Then:
        auto_aperture_mode = self._lewis.backdoor_get_from_device("auto_aperture_mode")
        self._lewis.assert_that_emulator_value_is(auto_aperture_mode, True)


@setup_tests
class ErrorTests(unittest.TestCase):

    def GIVEN_a_set_up_device_THEN_their_are_no_errors(self):
        # Then:
        expected_error_status = "No error"
        self.ca.assert_that_pv_is("ERROR", expected_error_status)
