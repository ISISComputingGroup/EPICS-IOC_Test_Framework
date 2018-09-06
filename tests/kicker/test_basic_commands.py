from parameterized import parameterized
import unittest

from utils.channel_access import ChannelAccess
from utils.testing import parameterized_list
from hamcrest import assert_that, is_, equal_to

DEVICE_PREFIX = "KICKER_01"

# VOLTAGE CALIBRATION CONSTANTS FOR TESTS
DAQ_MAX_VOLTAGE = 10.0
PSU_MAX_VOLTAGE = 45.0  # This is the default value set as a macro in IOC st.cmd
VOLTAGE_CALIBRATION_RATIO = PSU_MAX_VOLTAGE / DAQ_MAX_VOLTAGE

# CURRENT CALIBRATION CONSTANTS FOR TESTS
DAQ_MAX_CURRENT = 10.0
PSU_MAX_CURRENT = 15.0  # This is the default value set as a macro in IOC st.cmd
CURRENT_CALIBRATION_RATIO = PSU_MAX_CURRENT / DAQ_MAX_CURRENT


class BaseTests(unittest.TestCase):
    record = None
    calibration = None

    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")
        self._simulate_value(0)

    def _simulate_value(self, value):
        array_of_value = [value] * 1000
        pv_root = "DAQ:{}".format(self.record)
        self.ca.set_pv_value("{}:WV:SIM".format(pv_root), array_of_value)
        self.ca.assert_that_pv_is("{}:WV:SIM".format(pv_root), array_of_value)

        value_to_check = self.ca.get_pv_value("{}:_RAW".format(pv_root))
        assert_that(value_to_check, is_(equal_to(array_of_value)))

    @parameterized.expand(
        parameterized_list([4.68, 6, 10, 0, 4e-3])
    )
    def test_that_GIVEN_a_value_THEN_the_calibrated_value_is_read(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)

        # Then:
        expected_calibrated_value = self.calibration * value_to_set
        self.ca.assert_that_pv_is_number(self.record, expected_calibrated_value, 0.01)

    @parameterized.expand(
        parameterized_list([15, -5])
    )
    def test_that_GIVEN_a_value_out_of_range_THEN_the_pv_is_in_alarm(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)
        self.ca.assert_that_pv_is_number(self.record, value_to_set * self.calibration, 0.01)

        # Then:
        self.ca.assert_that_pv_alarm_is(self.record, self.ca.Alarms.MAJOR)

    @parameterized.expand(
        parameterized_list([10, 0])
    )
    def test_that_GIVEN_an_edge_value_THEN_the_pv_is_in_alarm(self, _, value_to_set):
        # Given:
        self._simulate_value(value_to_set)
        expected_calibrated_value = self.calibration * value_to_set
        self.ca.assert_that_pv_is_number(self.record, expected_calibrated_value, 0.01)

        # Then:
        self.ca.assert_that_pv_alarm_is(self.record, self.ca.Alarms.MAJOR)


class VoltageTests(BaseTests):
    record = "VOLT"
    calibration = VOLTAGE_CALIBRATION_RATIO


class CurrentTests(BaseTests):
    record = "CURR"
    calibration = CURRENT_CALIBRATION_RATIO

