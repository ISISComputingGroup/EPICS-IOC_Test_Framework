from __future__ import division

import unittest
from time import sleep
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "DMA4500M_01"
_EMULATOR_NAME = "dma4500m"

LEWIS_SPEED = 100
SCAN_FREQUENCY = 2

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DMA4500M"),
        "emulator": _EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.DEVSIM]


class DMA4500MTests(unittest.TestCase):
    """
    Tests for the DMA4500M density meter
    """

    PVS_ENABLED_OUTSIDE_MEASUREMENT = ["TEMPERATURE:SP", "START"]
    PVS_DISABLED_DURING_MEASUREMENT = ["TEMPERATURE:SP", "START", "AUTOMEASURE"]

    def _reset_ioc(self):
        self.ca.set_pv_value("MEASUREMENT", "ready")
        self.ca.set_pv_value("TEMPERATURE", 0)
        self.ca.set_pv_value("TEMPERATURE:SP", 0)
        self.ca.set_pv_value("DENSITY", 0)
        self.ca.set_pv_value("CONDITION", "0.00000")
        self.ca.set_pv_value("AUTOMEASURE:ENABLED", 0)
        self.ca.set_pv_value("AUTOMEASURE:FREQ:SP", 0)

    def _assert_pvs_disabled(self, pvs, disabled):
        for pv in pvs:
            self.ca.process_pv(pv)
            if disabled:
                self.ca.assert_that_pv_is("{0}.STAT".format(pv), "DISABLE")
            else:
                self.ca.assert_that_pv_is_not("{0}.STAT".format(pv), "DISABLE")

    def _start_instant_measurement(self):
        self._start_measurement(0)

    def _start_measurement(self, measurement_time=10):
        measurement_time = measurement_time
        self._lewis.backdoor_set_on_device("measurement_time", measurement_time * LEWIS_SPEED)
        self.ca.set_pv_value("START", 1)

    def _enable_automeasure(self, interval):
        self.ca.set_pv_value("AUTOMEASURE:FREQ:SP", interval)
        self.ca.set_pv_value("AUTOMEASURE:ENABLED", 1)

    def _disable_automeasure(self):
        self.ca.set_pv_value("AUTOMEASURE:ENABLED", 0)

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(_EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=15)
        self._lewis.backdoor_run_function_on_device("reset")
        self._reset_ioc()

    def test_WHEN_temperature_set_THEN_setpoint_readback_updates(self):
        self.ca.set_pv_value("TEMPERATURE:SP", 12.34)
        self.ca.assert_that_pv_is("TEMPERATURE:SP:RBV", 12.34)

    def test_WHEN_status_is_done_and_temperature_set_THEN_status_is_ready(self):
        self.ca.set_pv_value("MEASUREMENT", "done")
        self.ca.set_pv_value("TEMPERATURE:SP", 12.34)
        self.ca.assert_that_pv_is("MEASUREMENT", "ready")

    def test_WHEN_temperature_set_THEN_it_updates_after_measurement(self):
        self.ca.set_pv_value("TEMPERATURE:SP", 12.34)
        self._start_instant_measurement()
        self.ca.assert_that_pv_is("TEMPERATURE", 12.34)

    def test_WHEN_density_set_via_backdoor_THEN_it_updates_after_measurement(self):
        self._lewis.backdoor_set_on_device("density", 98.76)
        self._start_instant_measurement()
        self.ca.assert_that_pv_is("DENSITY", 98.76)

    def test_WHEN_condition_set_via_backdoor_THEN_it_updates_after_measurement(self):
        self._lewis.backdoor_set_on_device("condition", "valid")
        self._start_instant_measurement()
        self.ca.assert_that_pv_is("CONDITION", "valid")

    def test_WHEN_measurement_starts_THEN_status_updates(self):
        self._start_measurement(measurement_time=10)
        self.ca.assert_that_pv_is("MEASUREMENT", "measuring", timeout=SCAN_FREQUENCY)
        sleep(10)
        self.ca.assert_that_pv_is("MEASUREMENT", "done", timeout=SCAN_FREQUENCY)

    def test_WHEN_status_is_ready_THEN_correct_records_enabled(self):
        self._assert_pvs_disabled(self.PVS_ENABLED_OUTSIDE_MEASUREMENT, False)

    def test_WHEN_status_is_measuring_THEN_correct_records_disabled(self):
        self._start_measurement(measurement_time=10)
        self.ca.assert_that_pv_is("MEASUREMENT", "measuring", timeout=SCAN_FREQUENCY)
        self._assert_pvs_disabled(self.PVS_DISABLED_DURING_MEASUREMENT, True)

    def test_WHEN_status_is_done_THEN_correct_records_enabled(self):
        self._start_instant_measurement()
        self.ca.assert_that_pv_is("MEASUREMENT", "done", timeout=SCAN_FREQUENCY)
        self._assert_pvs_disabled(self.PVS_ENABLED_OUTSIDE_MEASUREMENT, False)

    @parameterized.expand(parameterized_list([2, 5, 10, 20]))
    def test_WHEN_automeasure_frequency_set_THEN_measurement_repeats(self, _, automeasure_interval):
        measurement_time = 5
        self._lewis.backdoor_set_on_device("measurement_time", measurement_time * LEWIS_SPEED)
        self._enable_automeasure(automeasure_interval)
        self.ca.assert_that_pv_is("MEASUREMENT", "measuring", timeout=2*automeasure_interval)
        self.ca.assert_that_pv_is("MEASUREMENT", "done", timeout=2*measurement_time)
        self.ca.assert_that_pv_is("MEASUREMENT", "measuring", timeout=2*automeasure_interval)

    @parameterized.expand(parameterized_list([2, 5, 10, 20]))
    def test_WHEN_automeasure_frequency_set_then_unset_THEN_measurement_stops(self, _, automeasure_interval):
        measurement_time = 5
        self._lewis.backdoor_set_on_device("measurement_time", measurement_time * LEWIS_SPEED)
        self._enable_automeasure(automeasure_interval)
        self.ca.assert_that_pv_is("MEASUREMENT", "measuring", timeout=2*automeasure_interval)
        self._disable_automeasure()
        self.ca.assert_that_pv_is("MEASUREMENT", "done", timeout=2*measurement_time)
        self.ca.assert_that_pv_is("MEASUREMENT", "done", timeout=2*automeasure_interval)

    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('MEASUREMENT', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('TEMPERATURE:SP:RBV', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('TEMPERATURE', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('DENSITY', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('CONDITION', ChannelAccess.Alarms.INVALID)
