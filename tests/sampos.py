import os
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, EPICS_TOP


DEVICE_PREFIX = "SAMPOS"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "SAMPOS", "iocBoot", "iocSAMPOS"),
        "macros": {},
    },
]


class SamposTests(unittest.TestCase):
    """
    Tests for the sampos IOC.
    """

    test_values = [0, 10]
    axes = ['X', 'Y', 'Z', 'W', 'S']

    def setUp(self):
        self._ioc = IOCRegister.get_running("SAMPOS")

        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self.ca.wait_for("DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_values_are_set_THEN_readbacks_update(self):
        for axis in self.axes:
            for value in self.test_values:
                self.ca.assert_setting_setpoint_sets_readback(value, readback_pv="{}".format(axis),
                                                              set_point_pv="{}:SP".format(axis))

    def test_WHEN_values_are_set_THEN_setpoint_readbacks_update(self):
        for axis in self.axes:
            for value in self.test_values:
                self.ca.assert_setting_setpoint_sets_readback(value, readback_pv="{}:SP:RBV".format(axis),
                                                              set_point_pv="{}:SP".format(axis))
