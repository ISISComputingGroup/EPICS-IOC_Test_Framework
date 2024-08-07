import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

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

MODES = ("Manual", "Auto")

CHANNELS = (
    "Channel 1",
    "Channel 2",
    "Channel 3",
)

CTRL_MODE_ALARMS = {
    "Locked": ChannelAccess.Alarms.NONE,
    "Remote only": ChannelAccess.Alarms.NONE,
    "Local only": ChannelAccess.Alarms.MAJOR,
    "Local and remote": ChannelAccess.Alarms.NONE,
}

# Build a list contain all the PVs that set a command and a set value
# product creates a cartesian product list of the two lists given
ALL_CONTROL_COMMANDS_LIST_OF_LISTS = [
    itertools.product(["P", "I", "D", "GASFLOW", "TEMP", "HEATERP"], TEST_VALUES),
    itertools.product(["MODE:HTR", "MODE:GAS"], MODES),
    itertools.product(["CTRLCHANNEL"], CHANNELS),
    itertools.product(["AUTOPID"], ["OFF", "ON"]),
]

ALL_CONTROL_COMMANDS = [
    command for command_list in ALL_CONTROL_COMMANDS_LIST_OF_LISTS for command in command_list
]


class Itc503Tests(unittest.TestCase):
    """
    Tests for the Itc503 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("itc503", DEVICE_PREFIX)
        self.ca = ChannelAccess(
            device_prefix=DEVICE_PREFIX, default_timeout=20, default_wait_time=0.0
        )
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
            for i in range(1, 8 + 1):
                # Ensure all DLY links are 0 in both FAN records
                self.ca.set_pv_value("FAN1.DLY{}".format(i), 0)
                self.ca.set_pv_value("FAN2.DLY{}".format(i), 0)

            # Set the scan rate to .1 second (setting string does not work, have to use numeric value)
            self.ca.set_pv_value("FAN1.SCAN", 9)

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand((pv, val) for pv, val in itertools.product(["P", "I", "D"], TEST_VALUES))
    def test_WHEN_setting_pid_settings_THEN_can_be_read_back(self, pv, val):
        self.ca.set_pv_value("{}:SP".format(pv), val)
        self.ca.assert_that_pv_is_number(pv, val, tolerance=0.1)  # Only comes back to 1dp

    @parameterized.expand(val for val in parameterized_list(TEST_VALUES))
    def test_WHEN_setting_flows_THEN_can_be_read_back(self, _, val):
        self.ca.set_pv_value("GASFLOW:SP", val)
        self.ca.assert_that_pv_is_number("GASFLOW", val, tolerance=0.1)  # Only comes back to 1dp

    @parameterized.expand(mode for mode in parameterized_list(MODES))
    def test_WHEN_setting_gas_flow_control_mode_THEN_can_be_read_back(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(mode, "MODE:GAS")

    @parameterized.expand(mode for mode in parameterized_list(MODES))
    def test_WHEN_setting_heater_flow_control_mode_THEN_can_be_read_back(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(mode, "MODE:HTR")

    @parameterized.expand(val for val in parameterized_list(TEST_VALUES))
    def test_WHEN_temperature_is_set_THEN_temperature_and_setpoint_readbacks_update_to_new_value(
        self, _, val
    ):
        self.ca.set_pv_value("TEMP:SP", val)
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number("TEMP:1", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number("TEMP:2", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number("TEMP:3", val, tolerance=0.1)

    @parameterized.expand(chan for chan in parameterized_list(CHANNELS))
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_control_channel_is_set_THEN_control_channel_can_be_read_back(self, _, chan):
        self.ca.assert_setting_setpoint_sets_readback(chan, "CTRLCHANNEL")

    @parameterized.expand(mode for mode in CTRL_MODE_ALARMS)
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_setting_control_mode_THEN_can_be_read_back(self, mode):
        self.ca.assert_setting_setpoint_sets_readback(
            mode, "CTRL", expected_alarm=CTRL_MODE_ALARMS[mode]
        )

    @skip_if_recsim("Backdoor does not exist in recsim")
    def test_WHEN_sweeping_mode_is_set_via_backdoor_THEN_it_updates_in_the_ioc(self):
        self._lewis.backdoor_set_on_device("sweeping", False)
        self.ca.assert_that_pv_is("SWEEPING", "Not Sweeping")

        self._lewis.backdoor_set_on_device("sweeping", True)
        self.ca.assert_that_pv_is("SWEEPING", "Sweeping")

    @parameterized.expand(state for state in ("ON", "OFF"))
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_setting_autopid_THEN_readback_reflects_setting_just_sent(self, state):
        self.ca.assert_setting_setpoint_sets_readback(state, "AUTOPID")

    @parameterized.expand(val for val in parameterized_list(TEST_VALUES))
    @skip_if_recsim("Backdoor does not exist in recsim")
    def test_WHEN_heater_voltage_is_set_THEN_heater_voltage_updates(self, _, val):
        self.ca.set_pv_value("HEATERP:SP", val)
        self.ca.assert_that_pv_is_number("HEATERP", val, tolerance=0.1)

        # Emulator responds with heater p == heater v. Test that heater p is also reading.
        self.ca.assert_that_pv_is_number("HEATERV", val, tolerance=0.1)

    @parameterized.expand(
        control_command for control_command in parameterized_list(ALL_CONTROL_COMMANDS)
    )
    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_control_command_sent_THEN_remote_unlocked_set(self, _, control_pv, set_value):
        self.ca.set_pv_value("CTRL", "Locked")
        self.ca.set_pv_value("{}:SP".format(control_pv), set_value)
        self.ca.assert_that_pv_is("CTRL", "Local and remote")
        self.ca.set_pv_value("CTRL", "Locked")

    @skip_if_recsim("Comes back via record redirection which recsim can't handle easily")
    def test_WHEN_sweeping_reported_by_hardware_THEN_correct_sweep_state_reported(self):
        """
        The hardware can report the control channel with and without a leading zero (depending on the hardware).
        Ensure we catch all cases.
        """
        for report_sweep_state_with_leading_zero in [True, False]:
            for sweeping in [True, False]:
                self._lewis.backdoor_set_on_device(
                    "report_sweep_state_with_leading_zero", report_sweep_state_with_leading_zero
                )
                self._lewis.backdoor_set_on_device("sweeping", sweeping)
                self.ca.assert_that_pv_is("SWEEPING", "Sweeping" if sweeping else "Not Sweeping")
