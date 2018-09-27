from __future__ import division
from parameterized import parameterized
import unittest


from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list


DEVICE_PREFIX = "SEPRTR_01"

MAX_DAQ_VOLT = 10
MAX_SEPARATOR_VOLT = 200
MIN_SEPARATOR_VOLT = 0
DAQ_VOLT_WRITE_SCALE_FACTOR = MAX_DAQ_VOLT / MAX_SEPARATOR_VOLT

MAX_SEPARATOR_CURR = 2.5
DAQ_CURR_READ_SCALE_FACTOR = MAX_SEPARATOR_CURR / MAX_DAQ_VOLT

MARGIN_OF_ERROR = 1e-5

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SEPRTR"),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM]

# Note that it is difficult to test the Current readback in Recsim because it is only a readback value, and relates
# closely to the voltage.


class PowerStatusTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self.ca.set_pv_value("VOLT:SP", 0)
        self.ca.assert_that_pv_is("VOLT:SP", 0)
        self.ca.assert_that_pv_is("POWER:STAT", "OFF")

    def test_that_GIVEN_psu_off_WHEN_voltage_setpoint_changed_higher_than_threshold_THEN_psu_status_changes_on(self):
        # GIVEN
        # asserted in setUp
        # WHEN
        self.ca.set_pv_value("VOLT:SP", 100)

        # THEN
        self.ca.assert_that_pv_is("POWER:STAT", "ON")

    def test_that_GIVEN_psu_on_WHEN_voltage_setpoint_changed_lower_than_threshold_THEN_psu_status_changes_off(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 10)
        self.ca.assert_that_pv_is("VOLT", 10)
        self.ca.assert_that_pv_is("POWER:STAT", "ON")

        # WHEN
        self.ca.set_pv_value("VOLT:SP", 0)

        # THEN
        self.ca.assert_that_pv_is("POWER:STAT", "OFF")


class VoltageTests(unittest.TestCase):
    voltage_values = [0, 10.1111111, 10e1, 20e-2, 200]
    voltage_values_which_give_alarms = [-50, MIN_SEPARATOR_VOLT, MAX_SEPARATOR_VOLT, 250]

    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self.ca.set_pv_value("VOLT:SP", 0)
        self.ca.assert_that_pv_is("VOLT:SP", 0)

    def test_that_GIVEN_sim_val_0_and_data_0_WHEN_voltage_set_point_changed_THEN_data_changed(self):
        # GIVEN
        self.ca.set_pv_value("DAQ:VOLT:SIM", 0)
        self.ca.assert_that_pv_is("DAQ:VOLT:SP:DATA", 0)

        # WHEN
        self.ca.set_pv_value("VOLT:SP", 20.)

        # THEN
        self.ca.assert_that_pv_is("DAQ:VOLT:SP:DATA", 20. * DAQ_VOLT_WRITE_SCALE_FACTOR)

    @parameterized.expand(parameterized_list(voltage_values))
    def test_that_WHEN_set_THEN_the_voltage_changes(self, _, value):
        # WHEN
        self.ca.set_pv_value("VOLT:SP", value)

        # THEN
        self.ca.assert_that_pv_is_number("VOLT", value, MARGIN_OF_ERROR)

    @parameterized.expand(parameterized_list(voltage_values_which_give_alarms))
    def test_that_WHEN_voltage_out_of_range_THEN_alarm_raised(self, _, value):
        # WHEN
        self.ca.set_pv_value("DAQ:VOLT:SP:DATA", value * DAQ_VOLT_WRITE_SCALE_FACTOR)
        self.ca.assert_that_pv_is("VOLT", value)

        # THEN
        self.ca.assert_that_pv_alarm_is("VOLT", ChannelAccess.Alarms.MAJOR)

    def test_that_GIVEN_voltage_in_range_WHEN_setpoint_is_above_range_THEN_setpoint_is_set_to_max_value(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 30)
        self.ca.assert_that_pv_is("VOLT", 30)

        # WHEN
        self.ca.set_pv_value("VOLT:SP", 215.)

        # THEN
        self.ca.assert_that_pv_is("VOLT:SP", MAX_SEPARATOR_VOLT)
        self.ca.assert_that_pv_is("VOLT", MAX_SEPARATOR_VOLT)

    def test_that_GIVEN_voltage_in_range_WHEN_setpoint_is_below_range_THEN_setpoint_is_set_to_min_value(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 30)
        self.ca.assert_that_pv_is("VOLT", 30)

        # WHEN
        self.ca.set_pv_value("VOLT:SP", -50)

        # THEN
        self.ca.assert_that_pv_is("VOLT", MIN_SEPARATOR_VOLT)
        self.ca.assert_that_pv_is("VOLT:SP", MIN_SEPARATOR_VOLT)


class CurrentTests(unittest.TestCase):
    # These current testing values are uncalibrated values from the DAQ lying between 0 and 10.
    current_values = [0, 1.33333, 5e1, 10e-3, 10]
    current_values_which_give_alarms = [-2, 0, 10, 11]

    def _simulate_current(self, current):
        curr_array = [current] * 1000
        self.ca.set_pv_value("DAQ:CURR:WV:SIM", curr_array)

    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._simulate_current(0)
        self.ca.assert_that_pv_is("CURR", 0)

    @parameterized.expand(parameterized_list(current_values))
    def test_that_GIVEN_current_value_THEN_calibrated_current_readback_changes(self, _, value):
        # GIVEN
        self._simulate_current(value)
        self.ca.assert_that_pv_is_number("CURR", value * DAQ_CURR_READ_SCALE_FACTOR, MARGIN_OF_ERROR)

    @parameterized.expand(parameterized_list(current_values_which_give_alarms))
    def test_that_WHEN_current_is_out_of_range_THEN_alarm_raised(self, _, value):
        # WHEN
        self._simulate_current(value)

        # THEN
        self.ca.assert_that_pv_alarm_is("CURR", ChannelAccess.Alarms.MAJOR)
