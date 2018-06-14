import os
import unittest

from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
from utils.ioc_launcher import EPICS_TOP


IOCS = [
    {
        "name": "GENESYS_01",
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "TDK_LAMBDA_GENESYS", "iocBoot", "iocGENESYS-IOC-01"),
        "macros": {
            "ADDR1": "1",
            "PORT1": "1",
        },
        "emulator": "tdk_lambda_genesys",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class OutputMode(object):
    VOLTAGE = "VOLTAGE"
    CURRENT = "CURRENT"


class TdkLambdaGenesysTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tdk_lambda_genesys", "GENESYS_01")
        self.ca = ChannelAccess(default_timeout=10, device_prefix="GENESYS_01")
        self.ca.wait_for("1:VOLT", timeout=20)

    def _write_voltage(self, expected_voltage):
        self._lewis.backdoor_set_on_device("voltage", expected_voltage)
        self.ca.set_pv_value("1:VOLT", expected_voltage)

    def _write_current(self, expected_current):
        self._lewis.backdoor_set_on_device("current", expected_current)
        self.ca.set_pv_value("1:CURR", expected_current)

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
                self._lewis.backdoor_set_on_device("current", curr)
                # Should be able to re-initialize comms and read the new current
                self.ca.assert_that_pv_is_number("1:CURR", curr, tolerance=0.01, timeout=30)

        finally:
            # If test fails, don't want it to affect other tests.
            self._lewis.backdoor_set_on_device("comms_initialized", True)
