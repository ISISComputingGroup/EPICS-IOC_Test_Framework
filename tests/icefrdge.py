import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc


DEVICE_PREFIX = "ICEFRDGE_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ICEFRDGE"),
        "macros": {},
        "emulator": "icefrdge",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class IceFridgeTests(unittest.TestCase):
    """
    Tests for the IceFrdge IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_auto_setpoint_THEN_set_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "AUTO:TEMP:SP:RBV", "AUTO:TEMP:SP")

    def test_WHEN_auto_setpoint_THEN_temperature_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "AUTO:TEMP", "AUTO:TEMP:SP")

    def test_WHEN_manual_setpoint_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "MANUAL:TEMP:SP:RBV", "MANUAL:TEMP:SP")

    def test_WHEN_manual_setpoint_THEN_temperature_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "MANUAL:TEMP", "MANUAL:TEMP:SP")
