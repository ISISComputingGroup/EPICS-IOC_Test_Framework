import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "SEPRTR_01"
DAQ = "DAQ"
MAX_DAQ_VOLT = 10.
MAX_SEPARATOR_VOLT = 200.
MAX_SEPARATOR_CURR = 2.5
DAQ_VOLT_SCALE_FACTOR = MAX_DAQ_VOLT / MAX_SEPARATOR_VOLT
DAQ_CURR_SCALE_FACTOR = MAX_DAQ_VOLT / MAX_SEPARATOR_CURR

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SEPRTR"),
        "macros": {"DAQMX": DAQ,
                   },
    },
]


TEST_MODES = [TestModes.RECSIM]

# Note that it is difficult to test the Current readback in Recsim because it is only a readback value, and relates
# closely to the voltage.


class PowerStatusTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        # self.ca.assert_that_pv_is("CURR:SP", 0)
        self.ca.set_pv_value("VOLT:SP", 0)
        self.ca.assert_that_pv_is("VOLT:SP", 0)

    def test_GIVEN_psu_off_WHEN_voltage_setpoint_changed_higher_than_threshold_THEN_psu_status_changes_on(self):
        # GIVEN
        # asserted in setUp
        # WHEN
        self.ca.set_pv_value("VOLT:SP", 100)
        # THEN
        self.ca.assert_that_pv_is("POWER", "ON")

    def test_GIVEN_psu_on_WHEN_voltage_setpoint_changed_lower_than_threshold_THEN_psu_status_changes_off(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 10)
        self.ca.assert_that_pv_is("VOLT", 10)
        self.ca.assert_that_pv_is("POWER", "ON")
        # WHEN
        self.ca.set_pv_value("VOLT:SP", 0)
        # THEN
        self.ca.assert_that_pv_is("POWER", "OFF")


class VoltageTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self.ca.set_pv_value("VOLT:SP", 0)
        self.ca.assert_that_pv_is("VOLT:SP", 0)

    def test_GIVEN_sim_val_0_and_acquire_not_processed_WHEN_voltage_set_point_changed_THEN_daq_acquire_processes_and_daq_data_changed(self):
        # GIVEN
        self.ca.set_pv_value("{}:VOLT:SIM".format(DAQ), 0)
        self.ca.assert_that_pv_is("{}:VOLT:SP:DATA".format(DAQ), 0)
        self.ca.set_pv_value("{}:VOLT:SP:ACQUIRE".format(DAQ), 0)
        self.ca.assert_that_pv_is("{}:VOLT:SP:ACQUIRE".format(DAQ), 'stop')

        # WHEN
        self.ca.set_pv_value("VOLT:SP", 20.)
        # THEN
        self.ca.assert_that_pv_is("{}:VOLT:SP:DATA".format(DAQ), 20. * DAQ_VOLT_SCALE_FACTOR)
        # self.ca.assert_that_pv_is("{}:VOLT:SP:CALC".format(DAQ), 1)
        # self.ca.assert_that_pv_is("{}:VOLT:SP:ACQUIRE".format(DAQ), 'run')

    def test_WHEN_set_THEN_the_voltage_changes(self):
        # WHEN
        self.ca.set_pv_value("VOLT:SP", 50.)
        # THEN
        self.ca.assert_that_pv_is("VOLT", 50.)

    def test_WHEN_setpoint_goes_above_range_THEN_triggers_alarm(self):
        # WHEN
        self.ca.set_pv_value("VOLT:SP", 215.)
        # THEN
        self.ca.assert_that_pv_alarm_is("VOLT", self.ca.Alarms.MINOR)

    def test_WHEN_setpoint_goes_below_range_THEN_triggers_alarm(self):
        # WHEN
        self.ca.set_pv_value("VOLT:SP", -15.)
        # THEN
        self.ca.assert_that_pv_alarm_is("VOLT", self.ca.Alarms.MINOR)
