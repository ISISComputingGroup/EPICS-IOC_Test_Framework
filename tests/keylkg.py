import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


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
        self.ca.set_pv_value("MODE:SP", "SET-UP")
        self.ca.set_pv_value("MEASUREMODE:HEAD:A:SP", 0)
        self.ca.set_pv_value("MEASUREMODE:HEAD:B:SP", 0)

    def test_GIVEN_running_ioc_WHEN_change_to_communication_mode_THEN_mode_changed(self):
        expected_value = "SET-UP"
        self.ca.set_pv_value("MODE:SP", expected_value)

        self.ca.assert_that_pv_is("MODE", expected_value, timeout=2)

    def test_GIVEN_running_ioc_WHEN_change_to_normal_mode_THEN_mode_changed(self):
        expected_value = "MEASURE"
        self.ca.set_pv_value("MODE:SP", expected_value)

        self.ca.assert_that_pv_is("MODE", expected_value, timeout=2)

    @parameterized.expand([('low limit', -99.9999), ('test_value_1', -2.3122), ('test_value_2', 12.3423), ('high limit', 99.9999)])
    def test_GIVE_running_ioc_WHEN_set_output1_offset_THEN_output1_offset_updated(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:1:SP", expected_value)

        self.ca.assert_that_pv_is("OFFSET:OUTPUT:1", expected_value, timeout=2)

    @parameterized.expand([('exceeds low limit', -100.0000), ('exceeds high limit', 100.000)])
    def test_GIVE_running_ioc_WHEN_set_output1_offset_outside_of_limits_THEN_output1_offset_within_limits(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:1:SP", expected_value)

        self.ca.assert_that_pv_is_an_integer_between("OFFSET:OUTPUT:1", -99.9999, 99.9999)

    @parameterized.expand([('low limit', -99.9999), ('test_value_1', -2.3122), ('test_value_2', 12.3423), ('high limit', 99.9999)])
    def test_GIVE_running_ioc_WHEN_set_output2_offset_THEN_output1_offset_updated(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:2:SP", expected_value)

        self.ca.assert_that_pv_is("OFFSET:OUTPUT:2", expected_value, timeout=2)

    @parameterized.expand([('exceeds low limit', -100.0000), ('exceeds high limit', 100.000)])
    def test_GIVE_running_ioc_WHEN_set_output2_offset_outside_of_limits_THEN_output2_offset_within_limits(self, _, mock_offset):
        expected_value = mock_offset
        self.ca.set_pv_value("OFFSET:OUTPUT:1:SP", expected_value)

        self.ca.assert_that_pv_is_an_integer_between("OFFSET:OUTPUT:2", -99.9999, 99.9999)

    def test_GIVEN_running_ioc_WHEN_change_to_head1_measurement_mode_THEN_mode_changed(self):
        expected_value = "MULTI-REFLECTIVE"
        self.ca.set_pv_value("MEASUREMODE:HEAD:A:SP", expected_value)

        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:A", expected_value, timeout=2)

    def test_GIVEN_running_ioc_WHEN_change_to_head2_measurement_mode_THEN_mode_changed(self):
        expected_value = "TRANSPARENT OBJ 1"
        self.ca.set_pv_value("MEASUREMODE:HEAD:B:SP", expected_value)

        self.ca.assert_that_pv_is("MEASUREMODE:HEAD:B", expected_value, timeout=2)

    @skip_if_recsim('Cannot use lewis backdoor in RECSIM')
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_THEN_output1_takes_data(self):
        expected_value = 0.1234
        self._lewis.backdoor_set_on_device("output1_raw_value", expected_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", expected_value, timeout=2)

    @skip_if_recsim('No emulation of data capture in RECSIM')
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_THEN_output2_takes_data(self):
        expected_value = 0.1234
        self._lewis.backdoor_set_on_device("output2_raw_value", expected_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", expected_value, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)

        self.ca.assert_that_pv_alarm_is('MODE:SP', ChannelAccess.Alarms.INVALID, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_device_not_connected_WHEN_get_error_THEN_alarm(self):
        expected_value = "ER,OF,00"
        self._lewis.backdoor_set_on_device('input_correct', False)

        self.ca.assert_that_pv_is_not("ERROR:STR", expected_value)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_and_reset_output1_THEN_output1_reset(self):
        expected_value = 0.0000
        test_value = 0.1234
        self._lewis.backdoor_set_on_device("output1_raw_value", test_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")
        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", test_value, timeout=2)
        self.ca.set_pv_value("RESET:OUTPUT:1:SP", "RESET")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", expected_value, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_and_reset_output2_THEN_output2_reset(self):
        expected_value = 0.0000
        test_value = 0.1234
        self._lewis.backdoor_set_on_device("output2_raw_value", test_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")
        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", test_value, timeout=2)
        self.ca.set_pv_value("RESET:OUTPUT:2:SP", "RESET")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", expected_value, timeout=2)

    @skip_if_recsim("Unable to use lewis backdoor in RECSIM")
    def test_GIVEN_running_ioc_WHEN_in_measure_mode_and_reset_both_outputs_THEN_both_outputs_reset(self):
        expected_value = 0.0000
        test_value = 0.1234
        self._lewis.backdoor_set_on_device("output1_raw_value", test_value)
        self._lewis.backdoor_set_on_device("output2_raw_value", test_value)
        self.ca.set_pv_value("MODE:SP", "MEASURE")
        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", test_value, timeout=2)
        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", test_value, timeout=2)
        self.ca.set_pv_value("RESET:OUTPUT:BOTH:SP", "RESET")

        self.ca.assert_that_pv_is("VALUE:OUTPUT:1", expected_value, timeout=2)
        self.ca.assert_that_pv_is("VALUE:OUTPUT:2", expected_value, timeout=2)