import unittest

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc


class EgxcolimTests(unittest.TestCase):
    """
    Tests for the egxcolim IOC.
    """

    directions = ["NORTH", "SOUTH"]
    axes = ["X"]

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("egxcolim")

        self.ca = ChannelAccess(20, device_prefix="EGXCOLIM")
        self.ca.wait_for("DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_setpoint_is_set_THEN_readback_updates(self):
        for direction in self.directions:
            for axis in self.axes:
                self.ca.assert_setting_setpoint_sets_readback(123, "{direction}:{axis}".format(direction=direction, axis=axis))

