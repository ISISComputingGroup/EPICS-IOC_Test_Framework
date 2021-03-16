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
        "emulator": "hlx503",
        "macros": {
            "SORB_CHANNEL": 1,
            "1KPOTHE3POTLO_CHANNEL": 2,
            "HE3POTHI_CHANNEL": 3,
            "SORB_SENSOR": 1,
            "1KPOTHE3POTLO_SENSOR": 2,
            "HE3POTHI_SENSOR": 3,
            "MAX_TEMP_FOR_HE3_COOLING": 2.0,
            "MAX_OPERATING_TEMP_FOR_HELIOX": 20.0
        }
    },
]


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class HLX503Tests(unittest.TestCase):
    """
    Tests for the ITC503/Heliox 3He Refrigerator.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("hlx503", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("backdoor_plug_in_he3potlow")

    @parameterized.expand(parameterized_list(["Auto", "Manual"]))
    def test_WHEN_set_autoheat_THEN_autoheat_set(self, _, value):
        self.ca.assert_setting_setpoint_sets_readback(value, "MODE:HTR")

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

    @parameterized.expand(parameterized_list(["SORB", "HE3POTHI", "1KPOTHE3POTLO"]))
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

    def test_WHEN_set_he3pot_temp_above_he3_cooling_threshold_THEN_he3pot_high_temp_set(self):
        self._lewis.backdoor_set_on_device("he3pot_temp", 1.5)
        self.ca.set_pv_value("TEMP:HE3POT:SP", 3.0)
        self.ca.assert_that_pv_is("CTRLCHANNEL", "HE3POTHI")
        self.ca.assert_that_pv_is("TEMP:HE3POTHI", 3.0)
        self.ca.assert_that_pv_is("TEMP:HE3POT", 3.0)

    def test_WHEN_set_he3pot_temp_below_he3_cooling_threshold_THEN_he3pot_low_temp_set(self):
        self._lewis.backdoor_set_on_device("he3pot_temp", 3.0)
        self.ca.set_pv_value("TEMP:HE3POT:SP", 1.0)
        self.ca.assert_that_pv_is("CTRLCHANNEL", "1KPOTHE3POTLO")
        self.ca.assert_that_pv_is("TEMP:1KPOTHE3POTLO", 1.0)
        self.ca.assert_that_pv_is("TEMP:HE3POT", 1.0)

    def test_WHEN_set_he3pot_temp_above_max_temp_threshold_THEN_he3pot_temp_not_set(self):
        he3pot_temp = self.ca.get_pv_value("TEMP:HE3POT")
        ctrl_channel = self.ca.get_pv_value("CTRLCHANNEL")
        self.ca.set_pv_value("TEMP:HE3POT:SP", 22.0)
        self.ca.assert_that_pv_alarm_is("TEMP:HE3POT:SP", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("CTRLCHANNEL", ctrl_channel)
        self.ca.assert_that_pv_is("TEMP:HE3POTHI", he3pot_temp)
        self.ca.assert_that_pv_is("TEMP:1KPOTHE3POTLO", he3pot_temp)
        self.ca.assert_that_pv_is("TEMP:HE3POT", he3pot_temp)

    # def test_GIVEN_he3pot_temp_above_he3_cooling_threshold_WHEN_turn_heater_off_THEN_heater_output_zero_AND_autoheat_off(self):
    #     # Arrange
    #     self.ca.set_pv_value("TEMP:HE3POT:SP", 3.0)
    #     self.ca.assert_that_pv_is("MODE:HTR", "Auto")
    #     # Act
    #     self.ca.process_pv("HEATER:HE3POT:OFF")
    #     # Assert
    #     self.ca.assert_that_pv_is("CTRLCHANNEL", "HE3POTHI")
    #     self.ca.assert_that_pv_is("MODE:HTR", "Manual")
    #     self.ca.assert_that_pv_is("HEATERP", 0.0)


    # def test_GIVEN_he3pot_temp_above_he3_cooling_threshold_WHEN_turn_heater_off_THEN_heater_output_zero_AND_autoheat_off(self):
    #     self.ca.set_pv_value("TEMP:HE3POT:SP", 3.0)
    #     self._lewis.backdoor_run_function_on_device("backdoor_set_port_heater", arguments=[2, 0, 0.0])
