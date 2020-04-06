from __future__ import division

import unittest
from time import sleep

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

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

    def _reset_ioc(self):
        self.ca.set_pv_value("MEASUREMENT", "ready")
        self.ca.set_pv_value("TEMPERATURE", 0)
        self.ca.set_pv_value("TEMPERATURE:SP", 0)
        self.ca.set_pv_value("DENSITY", 0)
        self.ca.set_pv_value("CONDITION", "0.00000")
        self.ca.set_pv_value("AUTOMEASURE:FREQ:SP", 0)

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
        self.ca.set_pv_value("START", 1)
        self.ca.assert_that_pv_is("TEMPERATURE", 12.34)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_density_set_via_backdoor_THEN_it_updates_after_measurement(self):
        self._lewis.backdoor_set_on_device("density", 98.76)
        self.ca.set_pv_value("START", 1)
        self.ca.assert_that_pv_is("DENSITY", 98.76)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_condition_set_via_backdoor_THEN_it_updates_after_measurement(self):
        self._lewis.backdoor_set_on_device("condition", "valid")
        self.ca.set_pv_value("START", 1)
        self.ca.assert_that_pv_is("CONDITION", "valid")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_measurement_starts_THEN_status_updates(self):
        measurement_time = 10
        self._lewis.backdoor_set_on_device("measurement_time", measurement_time * LEWIS_SPEED)
        self.ca.assert_that_pv_is("MEASUREMENT", "ready")
        self.ca.set_pv_value("START", 1)
        self.ca.assert_that_pv_is("MEASUREMENT", "measuring")
        sleep(measurement_time + SCAN_FREQUENCY)
        self.ca.assert_that_pv_is("MEASUREMENT", "done")

    def test_WHEN_automeasure_frequency_set_THEN_value_updates(self):
        self.ca.set_pv_value("AUTOMEASURE:FREQ:SP", 10)
        self.ca.assert_that_pv_is("AUTOMEASURE:FREQ", 10)

    @skip_if_recsim
    def test_WHEN_automeasure_frequency_set_THEN_measurement_starts(self):
        interval = 2
        measurement_time = 10
        self._lewis.backdoor_set_on_device("measurement_time", measurement_time * LEWIS_SPEED)
        self.ca.set_pv_value("AUTOMEASURE:FREQ:SP", interval)
        sleep(interval + SCAN_FREQUENCY)
        self.ca.assert_that_pv_is("MEASUREMENT", "measuring")

    @skip_if_recsim
    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('MEASUREMENT', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('TEMPERATURE:SP:RBV', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('TEMPERATURE', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('DENSITY', ChannelAccess.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is('CONDITION', ChannelAccess.Alarms.INVALID)
