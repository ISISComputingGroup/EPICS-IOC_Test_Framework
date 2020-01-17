from __future__ import division

import contextlib
import os
import unittest

from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
from utils.ioc_launcher import EPICS_TOP


AMPS_TO_GAUSS = 10

DEFAULT_READ_OFFSET = 0
DEFAULT_WRITE_OFFSET = 0

MAX_VOLTAGE = 200
MAX_CURRENT = 250


IOCS = [
    {
        "name": "GENESYS_01",
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "TDK_LAMBDA_GENESYS", "iocBoot", "iocGENESYS-IOC-01"),
        "macros": {
            "ADDR1": "1",
            "PORT1": "1",
            "AMPSTOGAUSS1": "{}".format(AMPS_TO_GAUSS),
            "TOLERANCE": 0.1,
            "READ_OFFSET1": DEFAULT_READ_OFFSET,
            "WRITE_OFFSET1": DEFAULT_WRITE_OFFSET,
            "MAX_VOLTAGE1": MAX_VOLTAGE,
            "MAX_CURRENT1": MAX_CURRENT,
        },
        "emulator": "tdk_lambda_genesys",
        "pv_for_existence": "1:CURR"
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class OutputMode(object):
    VOLTAGE = "VOLTAGE"
    CURRENT = "CURRENT"


class TdkLambdaGenesysTests(unittest.TestCase):

    @contextlib.contextmanager
    def _temporarily_change_offsets(self, read_offset, write_offset):
        self.ca.set_pv_value("1:CURR:_CALC.B", read_offset)
        self.ca.set_pv_value("1:CURR:SP:RBV:_CALC.B", read_offset)
        self.ca.set_pv_value("1:CURR:SP:_CALC.B", write_offset)
        try:
            yield
        finally:
            self.ca.set_pv_value("1:CURR:_CALC.B", DEFAULT_READ_OFFSET)
            self.ca.set_pv_value("1:CURR:SP:RBV:_CALC.B", DEFAULT_READ_OFFSET)
            self.ca.set_pv_value("1:CURR:SP:_CALC.B", DEFAULT_WRITE_OFFSET)

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tdk_lambda_genesys", "GENESYS_01")
        self.ca = ChannelAccess(default_timeout=10, device_prefix="GENESYS_01")
        self.ca.assert_that_pv_exists("1:VOLT", timeout=20)

    def _write_voltage(self, expected_voltage):
        self._lewis.backdoor_set_on_device("voltage", expected_voltage)
        self.ca.set_pv_value("1:SIM:VOLT", expected_voltage)

    def _write_current(self, expected_current):
        self._lewis.backdoor_set_on_device("current", expected_current)
        self.ca.set_pv_value("1:SIM:CURR", expected_current)

    def _set_power_state(self, expected_state):
        self._lewis.backdoor_set_on_device("powerstate", expected_state)

    @skip_if_recsim("Uses LeWIS backdoor")
    def test_GIVEN_voltage_set_WHEN_read_THEN_voltage_is_as_expected(self):
        expected_voltage = 4.3
        self._write_voltage(expected_voltage)
        self.ca.assert_that_pv_is("1:VOLT", expected_voltage)

    @skip_if_recsim("Uses LeWIS backdoor")
    def test_GIVEN_current_set_WHEN_read_THEN_current_is_as_expected(self):
        expected_current = 2
        self._write_current(expected_current)
        self.ca.assert_that_pv_is("1:CURR", expected_current)

    def test_GIVEN_setpoint_voltage_set_WHEN_read_THEN_setpoint_voltage_is_as_expected(self):
        expected_voltage = self.ca.get_pv_value("1:VOLT:SP") + 2.5
        self.ca.assert_setting_setpoint_sets_readback(expected_voltage, "1:VOLT:SP:RBV",
                                                      "1:VOLT:SP")

    def test_GIVEN_setpoint_current_set_when_read_THEN_setpoint_current_is_as_expected(self):
        expected_current = self.ca.get_pv_value("1:CURR:SP") + 5
        self.ca.assert_setting_setpoint_sets_readback(expected_current, "1:CURR:SP:RBV",
                                                      "1:CURR:SP")

    @skip_if_recsim("Uses LeWIS backdoor")
    def test_GIVEN_state_set_WHEN_read_THEN_state_is_as_expected_ON(self):
        self._set_power_state("ON")
        self.ca.assert_that_pv_is("1:POWER", "ON")

    @skip_if_recsim("Uses LeWIS backdoor")
    def test_GIVEN_state_set_WHEN_read_THEN_state_is_as_expected_OFF(self):
        self._set_power_state("OFF")
        self.ca.assert_that_pv_is("1:POWER", "OFF")

    def test_GIVEN_state_set_via_number_WHEN_read_THEN_state_is_as_expected(self):
        self.ca.set_pv_value("1:POWER:SP", 1)
        self.ca.assert_that_pv_is("1:POWER", "ON")

    @skip_if_recsim("Recsim is unable to simulate comms being uninitialized")
    def test_GIVEN_power_supply_comms_become_uninitialized_THEN_ioc_recovers(self):
        try:
            for curr in [0.123, 0.456]:
                self._lewis.backdoor_set_on_device("comms_initialized", False)
                self._write_current(curr)
                # Should be able to re-initialize comms and read the new current
                self.ca.assert_that_pv_is_number("1:CURR", curr, tolerance=0.01, timeout=30)

        finally:
            # If test fails, don't want it to affect other tests.
            self._lewis.backdoor_set_on_device("comms_initialized", True)

    def test_GIVEN_field_THEN_able_to_read_back(self):
        self.ca.assert_setting_setpoint_sets_readback(123, readback_pv="1:FIELD:SP:RBV", set_point_pv="1:FIELD:SP")

    @skip_if_recsim("Uses LeWIS backdoor")
    def test_GIVEN_current_THEN_able_to_field_correctly(self):
        test_value = 0.456
        self._lewis.backdoor_set_on_device("current", test_value)
        self.ca.assert_that_pv_is_number("1:CURR", test_value)
        self.ca.assert_that_pv_is_number("1:FIELD", test_value * AMPS_TO_GAUSS)

    def test_GIVEN_field_set_point_is_set_THEN_current_set_point_is_scaled_appropriately(self):
        test_value = 789
        self.ca.set_pv_value("1:FIELD:SP", test_value)
        self.ca.assert_that_pv_is_number("1:CURR:SP", test_value / AMPS_TO_GAUSS)

    @skip_if_recsim("Uses LeWIS backdoor")
    def test_GIVEN_current_set_point_THEN_field_set_point_RBV_is_read_correctly(self):
        test_value = 112.5
        self._lewis.backdoor_set_on_device("setpoint_current", test_value)
        self.ca.assert_that_pv_is_number("1:CURR:SP:RBV", test_value)
        self.ca.assert_that_pv_is_number("1:FIELD:SP:RBV",  test_value * AMPS_TO_GAUSS)

    @skip_if_recsim("Uses lewis backdoor")
    def test_GIVEN_non_zero_offsets_WHEN_setpoint_sent_to_psu_THEN_adjusted_by_offset(self):
        test_value = 25
        write_offset = 10
        with self._temporarily_change_offsets(read_offset=0, write_offset=write_offset):
            self.ca.set_pv_value("1:CURR:SP", test_value)
            self._lewis.assert_that_emulator_value_is("setpoint_current", test_value + write_offset, cast=float)

    @skip_if_recsim("Uses lewis backdoor")
    def test_GIVEN_non_zero_offsets_WHEN_value_read_back_from_psu_THEN_adjusted_by_offset(self):
        test_value = 43
        read_offset = 10
        with self._temporarily_change_offsets(read_offset=read_offset, write_offset=0):
            self._lewis.backdoor_set_on_device("current", test_value)
            self._lewis.backdoor_set_on_device("setpoint_current", test_value)

            self.ca.assert_that_pv_is_number("1:CURR", test_value + read_offset)
            self.ca.assert_that_pv_is_number("1:CURR:SP:RBV", test_value + read_offset)

    def test_GIVEN_voltage_setpoint_higher_than_max_THEN_capped_to_maximum_and_readback_alarm(self):
        self.ca.set_pv_value("1:VOLT:SP", MAX_VOLTAGE + 1)
        self.ca.assert_that_pv_is_number("1:VOLT:SP", MAX_VOLTAGE)
        self.ca.assert_that_pv_alarm_is("1:VOLT:SP:RBV", self.ca.Alarms.MINOR)

    def test_GIVEN_current_setpoint_higher_than_max_THEN_capped_to_maximum_and_readback_alarm(self):
        self.ca.set_pv_value("1:CURR:SP", MAX_CURRENT + 1)
        self.ca.assert_that_pv_is_number("1:CURR:SP", MAX_CURRENT)
        self.ca.assert_that_pv_alarm_is("1:CURR:SP:RBV", self.ca.Alarms.MINOR)

