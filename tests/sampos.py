import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class SamposTests(unittest.TestCase):
    """
    Tests for the sampos IOC.
    """

    test_values = [0, 10]
    axes = ['X', 'Y', 'Z', 'W', 'S']

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("sampos")

        self.ca = ChannelAccess(20)
        self.ca.wait_for("SAMPOS:DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("SAMPOS:DISABLE", "COMMS ENABLED")

    def test_WHEN_values_are_set_THEN_readbacks_update(self):
        for axis in self.axes:
            for value in self.test_values:
                self.ca.assert_setting_setpoint_sets_readback(value, readback_pv="SAMPOS:{}".format(axis),
                                                              set_point_pv="SAMPOS:{}:SP".format(axis))

    def test_WHEN_values_are_set_THEN_setpoint_readbacks_update(self):
        for axis in self.axes:
            for value in self.test_values:
                self.ca.assert_setting_setpoint_sets_readback(value, readback_pv="SAMPOS:{}:SP:RBV".format(axis),
                                                              set_point_pv="SAMPOS:{}:SP".format(axis))
