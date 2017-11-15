import unittest
from unittest import skipIf

import time
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister

# Internal Address of device (must be 2 characters)
ADDRESS = "A01"
# Numerical address of the device
ADDR_1 = 1
DEVICE_NAME = "EUROTHRM_01"
PREFIX = "{}:{}".format(DEVICE_NAME, ADDRESS)

# MACROS to use for the IOC
MACROS = {"ADDR": ADDRESS, "ADDR_1": ADDR_1}

# PV names
RBV_PV = "RBV"


class EurothermTests(unittest.TestCase):
    """
    Tests for the Eurotherm temperature controller.
    """

    def setUp(self):
        self._setup_lewis_and_channel_access()
        self._reset_device_state()

    def _setup_lewis_and_channel_access(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("eurotherm")
        self.ca = ChannelAccess(device_prefix=PREFIX)
        self.ca.wait_for(RBV_PV, timeout=30)
        self._lewis.backdoor_set_on_device("address", ADDRESS)

    def _reset_device_state(self):
        self._set_setpoint_and_current_temperature(0.0)
        self._lewis.backdoor_set_on_device("ramping_on", False)
        self._lewis.backdoor_set_on_device("ramp_rate", 1.0)
        self.ca.set_pv_value("RAMPON:SP", 0)

    def _set_setpoint_and_current_temperature(self, temperature):
        self._lewis.backdoor_set_on_device("current_temperature", temperature)
        self._lewis.backdoor_set_on_device("ramp_setpoint_temperature", temperature)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_read_rbv_temperature_THEN_rbv_value_is_same_as_backdoor(self):
        expected_temperature = 10.0
        self._set_setpoint_and_current_temperature(expected_temperature)
        self.ca.assert_that_pv_is(RBV_PV, expected_temperature)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_a_sp_WHEN_sp_read_rbv_temperature_THEN_rbv_value_is_same_as_sp(self):
        expected_temperature = 10.0
        self.ca.set_pv_value("SP", expected_temperature)
        self.ca.assert_that_pv_is("SP:RBV", expected_temperature)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_set_ramp_rate_in_K_per_min_THEN_current_temperature_reaches_set_point_in_expected_time(self):
        start_temperature = 5.0
        ramp_on = 1
        ramp_rate = 60.0
        setpoint_temperature = 25.0

        self._set_setpoint_and_current_temperature(start_temperature)
        self.ca.set_pv_value("TEMP:SP", start_temperature)

        self.ca.set_pv_value("RATE:SP", ramp_rate)
        self.ca.set_pv_value("RAMPON:SP", ramp_on)
        self.ca.set_pv_value("TEMP:SP", setpoint_temperature)

        start = time.time()
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", setpoint_temperature, timeout=60)
        end = time.time()
        self.assertAlmostEquals(end-start, 20, delta=1)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_sensor_disconnected_THEN_ramp_setting_is_disabled(self):
        sensor_disconnected_value = 1529

        self._lewis.backdoor_set_on_device("current_temperature", sensor_disconnected_value)

        self.ca.assert_that_pv_is_number("RAMPON:SP.DISP", 1)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_sensor_disconnected_WHEN_sensor_reconnected_THEN_ramp_setting_is_enabled(self):
        sensor_disconnected_value = 1529
        self._lewis.backdoor_set_on_device("current_temperature", sensor_disconnected_value)

        self._lewis.backdoor_set_on_device("current_temperature", 0)

        self.ca.assert_that_pv_is_number("RAMPON:SP.DISP", 0)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_ramp_was_off_WHEN_sensor_disconnected_THEN_ramp_is_off_and_cached_ramp_value_is_off(self):
        self.ca.set_pv_value("RAMPON:SP", 0)
        sensor_disconnected_value = 1529

        self._lewis.backdoor_set_on_device("current_temperature", sensor_disconnected_value)

        self.ca.assert_that_pv_is("RAMPON", "OFF")
        self.ca.assert_that_pv_is("RAMPON:CACHE", "OFF")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_ramp_was_on_WHEN_sensor_disconnected_THEN_ramp_is_off_and_cached_ramp_value_is_on(self):
        self.ca.set_pv_value("RAMPON:SP", 1)
        sensor_disconnected_value = 1529

        self._lewis.backdoor_set_on_device("current_temperature", sensor_disconnected_value)

        self.ca.assert_that_pv_is("RAMPON", "OFF")
        self.ca.assert_that_pv_is("RAMPON:CACHE", "ON")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_ramp_was_on_WHEN_sensor_disconnected_and_reconnected_THEN_ramp_is_on(self):
        self.ca.set_pv_value("RAMPON:SP", 1)
        sensor_disconnected_value = 1529

        self._lewis.backdoor_set_on_device("current_temperature", sensor_disconnected_value)
        self.ca.assert_that_pv_is("RAMPON", "OFF")
        self._lewis.backdoor_set_on_device("current_temperature", 0)

        self.ca.assert_that_pv_is("RAMPON", "ON")
