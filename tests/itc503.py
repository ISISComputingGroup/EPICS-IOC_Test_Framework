import unittest

import itertools
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "ITC503_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ITC503"),
        "macros": {},
        "emulator": "itc503",
    },
]


TEST_MODES = [TestModes.RECSIM]

TEST_VALUES = 0, 23.45


class Itc503Tests(unittest.TestCase):
    """
    Tests for the Itc503 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("itc503", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)
        self.ca.wait_for("SIM")
        self.ca.wait_for("DISABLE")

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_setting_pid_settings_THEN_can_be_read_back(self):
        for pv, value in itertools.product(["P", "I", "D"], TEST_VALUES):
            self.ca.assert_setting_setpoint_sets_readback(value, pv)

    def test_WHEN_setting_flows_THEN_can_be_read_back(self):
        for pv, value in itertools.product(["SHIELDFLW", "SAMPLEFLW"], TEST_VALUES):
            self.ca.assert_setting_setpoint_sets_readback(value, pv)

    def test_WHEN_setting_mode_THEN_can_be_read_back(self):
        for value in ("Auto", "Manual", "Auto"):
            self.ca.assert_setting_setpoint_sets_readback(value, "ACTIVITY")
