import os
import unittest

from parameterized import parameterized

from utils.emulator_launcher import CommandLineEmulatorLauncher
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

# Device prefix
DEVICE_PREFIX = "MEZFLIPR_01"
EMULATOR_NAME = "mezflipr"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MEZFLIPR"),
        "emulator": EMULATOR_NAME,
        "macros": {
            "PROTOCOL_VERSION": "2"
        }
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

# Currently only one flipper but they may add more in a future iteration of the program
flipper = "FLIPPER"


class MezfliprTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(["On", "Off"]))
    def test_GIVEN_power_is_set_THEN_can_be_read_back(self, _, state):
        self.ca.assert_setting_setpoint_sets_readback(state, readback_pv="{}:POWER".format(flipper))

    @parameterized.expand(parameterized_list([0., 0.12, 5000.5]))
    def test_GIVEN_compensation_is_set_THEN_compensation_can_be_read_back(self, _, compensation):
        self.ca.assert_setting_setpoint_sets_readback(compensation, readback_pv="{}:COMPENSATION".format(flipper))

    def _assert_mode(self, mode):
        self.ca.assert_that_pv_is("{}:MODE".format(flipper), mode)
        self.ca.assert_that_pv_alarm_is("{}:MODE".format(flipper), self.ca.Alarms.NONE)

    def _assert_params(self, param):
        self.ca.assert_that_pv_value_causes_func_to_return_true("{}:PARAMS".format(flipper),
                                                                lambda val: val is not None and val.rstrip() == param)
        self.ca.assert_that_pv_alarm_is("{}:PARAMS".format(flipper), self.ca.Alarms.NONE)

    @skip_if_recsim("State of device not simulated in recsim")
    def test_WHEN_constant_current_mode_set_THEN_parameters_reflected_and_mode_is_constant_current(self):
        param = 25
        self.ca.set_pv_value("{}:CURRENT:SP".format(flipper), param)

        self._assert_params("{:.1f}".format(param))
        self._assert_mode("static")

    @skip_if_recsim("State of device not simulated in recsim")
    def test_WHEN_steps_mode_set_THEN_parameters_reflected_and_mode_is_steps(self):
        param = "[some, random, list, of, data]"
        self.ca.set_pv_value("{}:CURRENT_STEPS:SP".format(flipper), param)

        self._assert_params(param)
        self._assert_mode("steps")

    @skip_if_recsim("State of device not simulated in recsim")
    def test_WHEN_analytical_mode_set_THEN_parameters_reflected_and_mode_is_analytical(self):
        param = "a long string of parameters which is longer than 40 characters"
        self.ca.set_pv_value("{}:CURRENT_ANALYTICAL:SP".format(flipper), param)

        self._assert_params(param)
        self._assert_mode("analytical")

    @skip_if_recsim("State of device not simulated in recsim")
    def test_WHEN_file_mode_set_THEN_parameters_reflected_and_mode_is_file(self):
        param = r"C:\some\file\path\to\a\file\in\a\really\deep\directory\structure\with\path\longer\than\40\characters"
        self.ca.set_pv_value("{}:FILENAME:SP".format(flipper), param)

        self._assert_params(param)
        self._assert_mode("file")

    @parameterized.expand(parameterized_list(["MODE", "COMPENSATION", "PARAMS"]))
    @skip_if_recsim("Recsim cannot test disconnected device")
    def test_WHEN_device_is_disconnected_THEN_pvs_are_in_invalid_alarm(self, _, pv):
        self.ca.assert_that_pv_alarm_is("{}:{}".format(flipper, pv), self.ca.Alarms.NONE)
        with self._lewis.backdoor_simulate_disconnected_device():
            self._lewis.backdoor_set_on_device("connected", False)
            self.ca.assert_that_pv_alarm_is("{}:{}".format(flipper, pv), self.ca.Alarms.INVALID)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is("{}:{}".format(flipper, pv), self.ca.Alarms.NONE)
