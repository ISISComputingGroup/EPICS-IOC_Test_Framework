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

TEST_VALUES = 0.12345678, 54.321

MODES = (
    "Manual",
    "Auto"
)

CHANNELS = (
    "Channel 1",
    "Channel 2",
    "Channel 3",
)


class Itc503Tests(unittest.TestCase):
    """
    Tests for the Itc503 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("itc503", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)
        self.ca.assert_that_pv_exists("DISABLE")
        self._make_device_scan_faster()

    def _make_device_scan_faster(self):
        """
        Purely so that the tests run faster, the real IOC scans excruciatingly slowly.
        """
        # Skip setting the PVs if the scan rate is already fast
        self.ca.assert_that_pv_exists("FAN1")
        self.ca.assert_that_pv_exists("FAN2")
        if self.ca.get_pv_value("FAN1.SCAN") != ".1 second":
            for i in range(1, 8+1):
                # Ensure all DLY links are 0 in both FAN records
                self.ca.set_pv_value("FAN1.DLY{}".format(i), 0)
                self.ca.set_pv_value("FAN2.DLY{}".format(i), 0)

            # Set the scan rate to .1 second (setting string does not work, have to use numeric value)
            self.ca.set_pv_value("FAN1.SCAN", 9)

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

    def test_WHEN_setting_gas_flow_control_mode_THEN_can_be_read_back(self):
        for mode in MODES:
            self.ca.assert_setting_setpoint_sets_readback(mode, "MODE:GAS")

    def test_WHEN_setting_heater_flow_control_mode_THEN_can_be_read_back(self):
        for mode in MODES:
            self.ca.assert_setting_setpoint_sets_readback(mode, "MODE:HTR")

    def test_WHEN_temperature_is_set_THEN_temperature_and_setpoint_readbacks_update_to_new_value(self):
        for value in TEST_VALUES:
            self.ca.set_pv_value("TEMP:SP", value)
            self.ca.assert_that_pv_is_number("TEMP:SP:RBV", value, tolerance=0.1)
            self.ca.assert_that_pv_is_number("TEMP:1", value, tolerance=0.1)
            self.ca.assert_that_pv_is_number("TEMP:2", value, tolerance=0.1)
            self.ca.assert_that_pv_is_number("TEMP:3", value, tolerance=0.1)

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_control_channel_is_set_THEN_control_channel_can_be_read_back(self):
        for chan in CHANNELS:
            self.ca.assert_setting_setpoint_sets_readback(chan, "CTRLCHANNEL")

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_setting_control_mode_THEN_can_be_read_back(self):
        for mode in ("Locked", "Remote only", "Local only", "Local and remote"):
            self.ca.assert_setting_setpoint_sets_readback(mode, "CTRL")

    @skip_if_recsim("Backdoor does not exist in recsim")
    def test_WHEN_sweeping_mode_is_set_via_backdoor_THEN_it_updates_in_the_ioc(self):
        self._lewis.backdoor_set_on_device("sweeping", False)
        self.ca.assert_that_pv_is("SWEEPING", "Not Sweeping")

        self._lewis.backdoor_set_on_device("sweeping", True)
        self.ca.assert_that_pv_is("SWEEPING", "Sweeping")

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_setting_autopid_THEN_readback_reflects_setting_just_sent(self):
        for state in ("ON", "OFF"):
            self.ca.assert_setting_setpoint_sets_readback(state, "AUTOPID")

    @skip_if_recsim("Backdoor does not exist in recsim")
    def test_WHEN_heater_voltage_is_set_THEN_heater_voltage_updates(self):
        for val in TEST_VALUES:
            self.ca.set_pv_value("HEATERV:SP", val)
            self.ca.assert_that_pv_is_number("HEATERV", val, tolerance=0.1)

            # Emulator responds with heater p == heater v. Test that heater p is also reading.
            self.ca.assert_that_pv_is_number("HEATERP", val, tolerance=0.1)
