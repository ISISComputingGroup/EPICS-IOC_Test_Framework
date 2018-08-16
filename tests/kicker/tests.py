from parameterized import parameterized
import unittest

from utils.channel_access import ChannelAccess
from utils.testing import parameterized_list

DEVICE_PREFIX = "KICKER_01"

# VOLTAGE CALIBRATION CONTSTANTS FOR TESTS
DAQ_MAX_VOLTAGE = 10.0
PSU_MAX_VOLTAGE = 45.0  # This is set as a macro in IOC st.cmd
VOLTAGE_CALIBRATION_RATIO = PSU_MAX_VOLTAGE / DAQ_MAX_VOLTAGE

# CURRENT CALIBRATION CONTSTANTS FOR TESTS
DAQ_MAX_CURRENT = 10.0
PSU_MAX_CURRENT = 15.0  # This is set as a macro in IOC st.cmd
CURRENT_CALIBRATION_RATIO = PSU_MAX_CURRENT / DAQ_MAX_CURRENT


class KickerBaseTests(unittest.TestCase):
    record = None
    channel = None
    calibration = None

    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)

    def set_value(self, value):
        pv_root = "DAQ:R0{}:DATA".format(self.channel)
        self.ca.set_pv_value("{}:SIM".format(pv_root), value)
        self.ca.assert_that_pv_is("{}:_RAW".format(pv_root), value)

    @parameterized.expand(
        parameterized_list([4.68, 10, 0, 4e-3])
    )
    def test_that_GIVEN_a_value_THEN_the_calibrated_value_is_read(self, _, value_to_set):
        # Given:
        self.set_value(value_to_set)

        # Then:
        expected_calibrated_value = self.calibration * value_to_set
        self.ca.assert_that_pv_is_number(self.record, expected_calibrated_value, 0.01)

    @parameterized.expand(
        parameterized_list([15, -5])
    )
    def test_that_GIVEN_a_value_out_of_range_THEN_pv_is_in_alarm(self, _, value_to_set):
        # Given:
        self.set_value(value_to_set)

        # Then:
        self.ca.assert_that_pv_alarm_is(self.record, self.ca.Alarms.MAJOR)


class KickerVoltageTests(KickerBaseTests):
    record = "VOLT"
    channel = 0
    calibration = VOLTAGE_CALIBRATION_RATIO


class KickerCurrentTests(KickerBaseTests):
    record = "CURR"
    channel = 2
    calibration = CURRENT_CALIBRATION_RATIO
