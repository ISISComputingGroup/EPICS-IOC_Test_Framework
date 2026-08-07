import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP, IOCRegister
from utils.test_modes import TestModes

DEVICE_PREFIX = "SAMPOS"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": (EPICS_TOP / "ioc" / "master" / "SAMPOS" / "iocBoot" / "iocSAMPOS").as_posix(),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM]


class SamposTests(unittest.TestCase):
    """
    Tests for the sampos IOC.
    """

    def setUp(self):
        self.test_values = [0, 10]
        self.axes = ["X", "Y", "Z", "W", "S"]
        self._ioc = IOCRegister.get_running("SAMPOS")

        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_values_are_set_THEN_readbacks_update(self):
        for axis in self.axes:
            for value in self.test_values:
                self.ca.assert_setting_setpoint_sets_readback(
                    value, readback_pv=f"{axis}", set_point_pv=f"{axis}:SP"
                )

    def test_WHEN_values_are_set_THEN_setpoint_readbacks_update(self):
        for axis in self.axes:
            for value in self.test_values:
                self.ca.assert_setting_setpoint_sets_readback(
                    value, readback_pv=f"{axis}:SP:RBV", set_point_pv=f"{axis}:SP"
                )
