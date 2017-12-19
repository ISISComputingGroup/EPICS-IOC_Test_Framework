import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "TRITON_01"

PID_TEST_VALUES = 0, 10**-5, 123.45, 10**5
TEMPERATURE_TEST_VALUES = 0, 10**-5, 5.4321, 1000
HEATER_RANGE_TEST_VALUES = 0.001, 0.316, 1000


class TritonTests(unittest.TestCase):
    """
    Tests for the Triton IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("triton")
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skipIf(IOCRegister.uses_rec_sim, "Not implemented in recsim")
    def test_WHEN_device_is_started_THEN_can_get_mixing_chamber_uid(self):
        self.ca.assert_that_pv_is("MC:UID", "mix_chamber_name")

    def test_WHEN_P_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "P")

    def test_WHEN_I_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "I")

    def test_WHEN_D_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "D")

    def test_WHEN_temperature_setpoint_is_set_THEN_readback_updates(self):
        for value in TEMPERATURE_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, set_point_pv="TEMP:SP", readback_pv="TEMP:SP:RBV")

    def test_WHEN_heater_range_is_set_THEN_readback_updates(self):
        for value in HEATER_RANGE_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "HEATER:RANGE")
