import unittest

import itertools
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, skip_if_devsim

DEVICE_PREFIX = "ITC503_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ITC503"),
        "emulator": "itc503",
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]

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
            self.ca.set_pv_value("{}:SP".format(pv), value)
            self.ca.assert_that_pv_is_number(pv, value, tolerance=0.1)  # Only comes back to 1dp

    def test_WHEN_setting_flows_THEN_can_be_read_back(self):
        for value in TEST_VALUES:
            self.ca.set_pv_value("GASFLOW:SP", value)
            self.ca.assert_that_pv_is_number("GASFLOW", value, tolerance=0.1)  # Only comes back to 1dp

    def test_WHEN_setting_mode_THEN_can_be_read_back(self):
        for value in ("Auto", "Manual", "Auto"):
            self.ca.assert_setting_setpoint_sets_readback(value, "ACTIVITY")

    def test_WHEN_temperature_is_set_THEN_temperature_and_setpoint_readbacks_update_to_new_value(self):
        for value in TEST_VALUES:
            self.ca.set_pv_value("TEMP:SP", value)
            self.ca.assert_that_pv_is_number("TEMP", value, tolerance=0.1)
            self.ca.assert_that_pv_is_number("TEMP:SP:RBV", value, tolerance=0.1)

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_setting_control_mode_THEN_can_be_read_back(self):
        for chan in ("FPLock", "EPICS+FPLock", "FPUnlock", "EPICS+FPUnlock"):
            self.ca.assert_setting_setpoint_sets_readback(chan, "CTRL")

    @skip_if_recsim("Backdoor does not exist in recsim")
    def test_WHEN_sweeping_mode_is_set_via_backdoor_THEN_it_updates_in_the_ioc(self):
        self._lewis.backdoor_set_on_device("sweeping", False)
        self.ca.assert_that_pv_is("SWEEPING", "Not Sweeping")

        self._lewis.backdoor_set_on_device("sweeping", True)
        self.ca.assert_that_pv_is("SWEEPING", "Sweeping")
