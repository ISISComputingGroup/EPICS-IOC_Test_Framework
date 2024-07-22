import os
import unittest

import sys

from parameterized import parameterized

from utils.emulator_launcher import CommandLineEmulatorLauncher, DEFAULT_PY_PATH
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc, parameterized_list

# Device prefix
DEVICE_PREFIX = "MEZFLIPR_01"
EMULATOR_NAME = "mezflipr"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MEZFLIPR"),
        "emulator": EMULATOR_NAME,
        "emulator_launcher_class": CommandLineEmulatorLauncher,
        "emulator_command_line": "{} {} --port {{port}}".format(
            os.path.join(DEFAULT_PY_PATH, "python.exe"),
            os.path.join(
                EPICS_TOP,
                "support",
                "deviceemulator",
                "master",
                "other_emulators",
                "mezei_flipper",
                "flipper_emulator.py",
            ),
        ),
        "macros": {
            "POLARISERPRESENT": "yes",
            "ANALYSERPRESENT": "yes",
            "PROTOCOL_VERSION": "1",
        },
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class MezfliprTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skip_if_recsim("Disconnection simulation not implemented in recsim")
    def test_GIVEN_device_is_connected_THEN_can_read_id(self):
        self.ca.assert_that_pv_is("ID", "Flipper Control")
        self.ca.assert_that_pv_alarm_is("ID", self.ca.Alarms.NONE)

    @parameterized.expand(["ANALYSER", "POLARISER"])
    def test_GIVEN_amplitude_is_set_THEN_amplitude_can_be_read_back(self, flipper):
        for val in [0.0, 0.12, 2.99]:  # Amplitude should be limited to 3A
            self.ca.assert_setting_setpoint_sets_readback(
                val, readback_pv="{}:AMPLITUDE".format(flipper)
            )

    @parameterized.expand(["ANALYSER", "POLARISER"])
    def test_GIVEN_compensation_is_set_THEN_compensation_can_be_read_back(self, flipper):
        for val in [0.0, 0.12, 5000.5]:
            self.ca.assert_setting_setpoint_sets_readback(
                val, readback_pv="{}:COMPENSATION".format(flipper)
            )

    @parameterized.expand(["ANALYSER", "POLARISER"])
    def test_GIVEN_dt_is_set_THEN_dt_can_be_read_back(self, flipper):
        for val in [0.0, -0.12, -5000.5]:  # DT only accepts negative values.
            self.ca.assert_setting_setpoint_sets_readback(val, readback_pv="{}:DT".format(flipper))

    @parameterized.expand(["ANALYSER", "POLARISER"])
    def test_GIVEN_constant_is_set_THEN_constant_can_be_read_back(self, flipper):
        for val in [0.0, 0.12, 5000.5]:
            self.ca.assert_setting_setpoint_sets_readback(
                val, readback_pv="{}:CONSTANT".format(flipper)
            )

    @parameterized.expand(["ANALYSER", "POLARISER"])
    def test_GIVEN_constant_is_set_THEN_constant_can_be_read_back(self, flipper):
        for filename in [r"C:\a.txt", r"C:\b.txt"]:
            self.ca.assert_setting_setpoint_sets_readback(
                filename, readback_pv="{}:FILENAME".format(flipper)
            )

    @parameterized.expand(
        [
            "Analyser Off Pol. Off",
            "Analyser Off Pol. On",
            "Analyser On Pol. Off",
            "Analyser On Pol. On",
        ]
    )
    def test_GIVEN_toggle_state_is_set_THEN_toggle_state_can_be_read_back(self, toggle_state):
        self.ca.set_pv_value("TOGGLE:SP", toggle_state)
        self.ca.assert_that_pv_is("TOGGLE", toggle_state)
        self.ca.assert_that_pv_alarm_is("TOGGLE", self.ca.Alarms.NONE)
