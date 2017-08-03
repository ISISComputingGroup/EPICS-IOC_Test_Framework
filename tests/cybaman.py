import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class CybamanTests(unittest.TestCase):
    """
    Tests for the cybaman IOC.
    """

    AXES = ["A", "B", "C"]
    test_positions = [-100, -1.23, 0, 180.0]

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("cybaman")

        self.ca = ChannelAccess(20)
        self.ca.wait_for("CYBAMAN_01:INITIALIZE", timeout=30)


    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("CYBAMAN_01:DISABLE", "COMMS ENABLED")


    @skipIf(IOCRegister.uses_rec_sim, "Uses lewis backdoor command")
    def test_WHEN_positions_are_set_via_backdoor_THEN_positions_are_reported_correctly(self):
        for axis in self.AXES:
            for pos in self.test_positions:
                self._lewis.backdoor_set_on_device("{}".format(axis.lower()), pos)
                self.ca.assert_that_pv_is_number("CYBAMAN_01:{}".format(axis), pos, tolerance=0.01)

