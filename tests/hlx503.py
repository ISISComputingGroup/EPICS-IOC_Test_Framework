import unittest

from parameterized import parameterized

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, parameterized_list

# Device prefix
DEVICE_PREFIX = "HLX503_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HLX503"),
        "emulator": "itc503",
        "macros": {}
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ITC503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("itc503", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    @parameterized.expand(parameterized_list(["Auto", "Manual"]))
    def test_WHEN_set_autoheat_THEN_autoheat_set(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(value, "MODE:HTR")

    @parameterized.expand(parameterized_list(["Auto", "Manual"]))
    def test_WHEN_set_autoneedlevalue_AND_THEN_autoneedlevalve_set(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(value, "MODE:GAS")

    @parameterized.expand(parameterized_list(["ON", "OFF"]))
    def test_WHEN_set_autopid_AND_THEN_autopid_set(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(value, "AUTOPID")

    @parameterized.expand(parameterized_list(["Locked", "Remote only", "Local only", "Local and remote"]))
    def test_WHEN_set_remote_THEN_remote_set(self, _, value):
        expected_alarm = self.ca.Alarms.NONE if value != "Local only" else self.ca.Alarms.MAJOR
        self.ca.assert_setting_setpoint_sets_readback(value, "CTRL", expected_alarm=expected_alarm)

    @parameterized.expand(parameterized_list([2.4, 18.3]))
    def test_WHEN_temp_set_THEN_temp_sp_rbv_correct(self, _, val):
        self.ca.set_pv_value("TEMP:SP", val)
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number("TEMP:1", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number("TEMP:2", val, tolerance=0.1)
        self.ca.assert_that_pv_is_number("TEMP:3", val, tolerance=0.1)

    @parameterized.expand(parameterized_list(["Channel 1", "Channel 2", "Channel 3"]))
    def test_WHEN_ctrlchannel_set_THEN_ctrlchannel_set(self, _, new_control_channel):
        self.ca.assert_setting_setpoint_sets_readback(new_control_channel, "CTRLCHANNEL")

    @parameterized.expand(parameterized_list([0.2, 3.8]))
    def test_WHEN_proportional_set_THEN_proportional_set(self, _, proportional):
        self.ca.assert_setting_setpoint_sets_readback(proportional, "P")

    @parameterized.expand(parameterized_list([0.2, 3.8]))
    def test_WHEN_integral_set_THEN_integral_set(self, _, integral):
        self.ca.assert_setting_setpoint_sets_readback(integral, "I")

    @parameterized.expand(parameterized_list([0.2, 3.8]))
    def test_WHEN_derivative_set_THEN_derivative_set(self, _, derivative):
        self.ca.assert_setting_setpoint_sets_readback(derivative, "D")

    @parameterized.expand(parameterized_list([23.2, 87.1]))
    def test_WHEN_heater_output_set_THEN_heater_output_set(self, _, heater_output):
        self.ca.assert_setting_setpoint_sets_readback(heater_output, "HEATERP")

    @parameterized.expand(parameterized_list([31.9, 66.6]))
    def test_WHEN_gasflow_set_THEN_gasflow_set(self, _, percent):
        self.ca.assert_setting_setpoint_sets_readback(percent, "GASFLOW")
