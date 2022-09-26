import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list


DEVICE_PREFIX = "KEYLKG_01"
EMULATOR_NAME = "keylkg"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEYLKG"),
        "macros": {},
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class KeylkgTests(unittest.TestCase):
    """
    Tests for the Keylkg IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset")

    def test_GIVEN_running_ioc_WHEN_change_to_communication_mode_THEN_mode_changed(self):
        expected_value = "SET-UP"
        self.ca.set_pv_value("MODE:SP", expected_value)

        self.ca.assert_that_pv_is("MODE", expected_value)

    def test_GIVEN_running_ioc_WHEN_change_to_normal_mode_THEN_mode_changed(self):
        expected_value = "MEASURE"
        self.ca.set_pv_value("MODE:SP", expected_value)

        self.ca.assert_that_pv_is("MODE", expected_value)

    @parameterized.expand([('low limit', -99.9999), ('test_value_1', -2.3122), ('test_value_2', 12.3423), ('high limit', 99.9999)])
    def test_GIVEN_running_ioc_WHEN_set_output1_offset_THEN_output1_offset_updated(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:1:SP", expected_value)

        self.ca.assert_that_pv_is_number("OFFSET:OUTPUT:1", expected_value, tolerance=0.001)

    @parameterized.expand([('exceeds low limit', -100.0000), ('exceeds high limit', 100.000)])
    def test_GIVEN_running_ioc_WHEN_set_output1_offset_outside_of_limits_THEN_output1_offset_within_limits(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:1:SP", expected_value)

        self.ca.assert_that_pv_is_within_range("OFFSET:OUTPUT:1", -99.9999, 99.9999)

    @parameterized.expand([('low limit', -99.9999), ('test_value_1', -2.3122), ('test_value_2', 12.3423), ('high limit', 99.9999)])
    def test_GIVEN_running_ioc_WHEN_set_output2_offset_THEN_output1_offset_updated(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:2:SP", expected_value)

        self.ca.assert_that_pv_is_number("OFFSET:OUTPUT:2", expected_value, tolerance=0.001)

    @parameterized.expand([('exceeds low limit', -100.0000), ('exceeds high limit', 100.000)])
    def test_GIVEN_running_ioc_WHEN_set_output2_offset_outside_of_limits_THEN_output2_offset_within_limits(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:1:SP", expected_value)

        self.ca.assert_that_pv_is_within_range("OFFSET:OUTPUT:2", -99.9999, 99.9999)

    def test_GIVEN_running_ioc_WHEN_change_to_head1_measurement_mode_THEN_mode_changed(self):
        expected_value = "MULTI-REFLECTIVE"
        self.ca.set_pv_value("MEASUREMODE:HEAD:A:SP", expected_value)

        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:A", expected_value)

    def test_GIVEN_running_ioc_WHEN_change_to_head2_measurement_mode_THEN_mode_changed(self):
        expected_value = "TRANSPARENT OBJ 1"
        self.ca.set_pv_value("MEASUREMODE:HEAD:B:SP", expected_value)

        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:B", expected_value)

    @skip_if_recsim('Cannot use lewis backdoor in RECSIM')
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_THEN_output1_takes_data(self):
        expected_value = 0.1234
        self._lewis.backdoor_set_on_device("detector_1_raw_value", expected_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", expected_value)

    @skip_if_recsim('No emulation of data capture in RECSIM')
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_THEN_output2_takes_data(self):
        expected_value = 0.1234
        self._lewis.backdoor_set_on_device("detector_2_raw_value", expected_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        self.ca.assert_that_pv_alarm_is('MODE:SP', ChannelAccess.Alarms.NONE)
        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is('MODE:SP', ChannelAccess.Alarms.INVALID)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is('MODE:SP', ChannelAccess.Alarms.NONE)


    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        expected_value = "Command error"
        self._lewis.backdoor_set_on_device('input_correct', False)

        self.ca.assert_that_pv_is_not("ERROR", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_and_reset_output1_THEN_output1_reset(self):
        expected_value = 0.0000
        test_value = 0.1234
        self._lewis.backdoor_set_on_device("detector_1_raw_value", test_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")
        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", test_value)
        self.ca.set_pv_value("RESET:OUTPUT:1:SP", "RESET")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_and_reset_output2_THEN_output2_reset(self):
        expected_value = 0.0000
        test_value = 0.1234
        self._lewis.backdoor_set_on_device("detector_2_raw_value", test_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")
        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", test_value)
        self.ca.set_pv_value("RESET:OUTPUT:2:SP", "RESET")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", expected_value)

    @skip_if_recsim('Cannot use lewis backdoor in RECSIM')
    def test_GIVEN_running_ioc_WHEN_in_setup_mode_THEN_output1_switches_to_measurement_mode_and_takes_data(self):
        expected_value = 0.1234
        self.ca.set_pv_value("MODE:SP", "SET-UP")
        self._lewis.backdoor_set_on_device("detector_1_raw_value", expected_value)

        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", expected_value)

    @parameterized.expand(parameterized_list(["Passive", "5 second"]))
    @skip_if_recsim("Scan rate changes do not work in RECSIM.")
    def test_WHEN_scan_rates_changed_THEN_scan_rates_set_correctly(self, _, rate):
        self.ca.set_pv_value("SCAN:SP", rate)
        self.ca.assert_that_pv_is("OFFSET:OUTPUT:1.SCAN", rate)
        self.ca.assert_that_pv_is("OFFSET:OUTPUT:2.SCAN", rate)
        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:A.SCAN", rate)
        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:B.SCAN", rate)
