from hamcrest import assert_that, is_, equal_to
from parameterized import parameterized
import unittest

from utils.channel_access import ChannelAccess
from utils.testing import parameterized_list, add_method

from . import DEVICE_PREFIX

# VOLTAGE CALIBRATION CONSTANTS FOR TESTS
DAQ_MAX_VOLTAGE = 10.0
PSU_MAX_VOLTAGE = 45.0  # This is the default value set as a macro in IOC st.cmd
VOLTAGE_CALIBRATION_RATIO = PSU_MAX_VOLTAGE / DAQ_MAX_VOLTAGE

# CURRENT CALIBRATION CONSTANTS FOR TESTS
DAQ_MAX_CURRENT = 10.0
PSU_MAX_CURRENT = 15.0  # This is the default value set as a macro in IOC st.cmd
CURRENT_CALIBRATION_RATIO = PSU_MAX_CURRENT / DAQ_MAX_CURRENT


def setUp(self):
    self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
    self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")
    self._simulate_value(0)


@add_method(setUp)
class VoltageTests(unittest.TestCase):

    def _simulate_value(self, value):
        array_of_value = [value] * 1000
        pv_root = "DAQ:VOLT"
        self.ca.set_pv_value("{}:WV:SIM".format(pv_root), array_of_value)
        self.ca.assert_that_pv_is("{}:WV:SIM".format(pv_root), array_of_value)

        value_to_check = self.ca.get_pv_value("{}:_RAW".format(pv_root))
        assert_that(value_to_check, is_(equal_to(array_of_value)))

    @parameterized.expand(
        parameterized_list([5.86, 6.7893651, 2, 10, 0, 4e-3])
    )
    def test_that_GIVEN_a_voltage_THEN_the_a_calibrated_voltage_of_the_PSU_is_read(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)

        # Then:
        expected_calibrated_voltage = VOLTAGE_CALIBRATION_RATIO * value_to_set
        self.ca.assert_that_pv_is_number("VOLT", expected_calibrated_voltage, 0.01)

    @parameterized.expand(
        parameterized_list([12, -6])
    )
    def test_that_GIVEN_a_voltage_out_of_range_THEN_the_voltage_pv_is_in_alarm(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)
        calibrated_value = VOLTAGE_CALIBRATION_RATIO * value_to_set
        self.ca.assert_that_pv_is_number("VOLT", calibrated_value, 0.01)

        # Then:
        self.ca.assert_that_pv_alarm_is("VOLT", self.ca.Alarms.MAJOR)

    @parameterized.expand(
        parameterized_list([10, 0])
    )
    def test_that_GIVEN_an_edge_case_voltage_THEN_then_the_voltage_pv_is_in_alarm(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)
        expected_calibrated_value = VOLTAGE_CALIBRATION_RATIO * value_to_set
        self.ca.assert_that_pv_is_number("VOLT", expected_calibrated_value, 0.01)

        # Then:
        self.ca.assert_that_pv_alarm_is("VOLT", self.ca.Alarms.MAJOR)


@add_method(setUp)
class CurrentTests(unittest.TestCase):

    def _simulate_value(self, value):
        array_of_value = [value] * 1000
        pv_root = "DAQ:CURR"
        self.ca.set_pv_value("{}:WV:SIM".format(pv_root), array_of_value)
        self.ca.assert_that_pv_is("{}:WV:SIM".format(pv_root), array_of_value)

        value_to_check = self.ca.get_pv_value("{}:_RAW".format(pv_root))
        assert_that(value_to_check, is_(equal_to(array_of_value)))

    @parameterized.expand(
        parameterized_list([5.78962156, 8.62, 1, 10, 0, 8e-3])
    )
    def test_that_GIVEN_a_current_THEN_the_calibrated_current_of_the_PSU_is_read(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)

        # Then:
        expected_calibrated_value = CURRENT_CALIBRATION_RATIO * value_to_set
        self.ca.assert_that_pv_is_number("CURR", expected_calibrated_value, 0.01)

    @parameterized.expand(
        parameterized_list([12, -3])
    )
    def test_that_GIVEN_a_current_value_out_of_range_THEN_the_current_pv_is_in_alarm(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)
        self.ca.assert_that_pv_is_number("CURR", value_to_set * CURRENT_CALIBRATION_RATIO, 0.01)

        # Then:
        self.ca.assert_that_pv_alarm_is("CURR", self.ca.Alarms.MAJOR)

    @parameterized.expand(
        parameterized_list([10, 0])
    )
    def test_that_GIVEN_an_edge_value_THEN_the_pv_is_in_alarm(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)
        expected_calibrated_value = CURRENT_CALIBRATION_RATIO * value_to_set
        self.ca.assert_that_pv_is_number("CURR", expected_calibrated_value, 0.01)

        # Then:
        self.ca.assert_that_pv_alarm_is("CURR", self.ca.Alarms.MAJOR)
