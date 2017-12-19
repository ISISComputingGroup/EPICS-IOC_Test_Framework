import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "TRITON_01"


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
        self.ca.assert_setting_setpoint_sets_readback(5, "P")

    def test_WHEN_I_setpoint_is_set_THEN_readback_updates(self):
        self.ca.assert_setting_setpoint_sets_readback(5, "I")

    def test_WHEN_D_setpoint_is_set_THEN_readback_updates(self):
        self.ca.assert_setting_setpoint_sets_readback(5, "D")
