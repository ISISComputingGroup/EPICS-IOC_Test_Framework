import os
import unittest

import sys

from parameterized import parameterized

from utils.emulator_launcher import CommandLineEmulatorLauncher
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
            sys.executable,
            os.path.join(EPICS_TOP, "support", "deviceemulator", "master", "other_emulators", "mezei_flipper", "flipper_emulator.py")
        )
    },
]


TEST_MODES = [TestModes.DEVSIM]


class MezfliprTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @skip_if_recsim("Disconnection simulation not implemented in recsim")
    def test_GIVEN_device_is_connected_THEN_can_read_id(self):
        self.ca.assert_that_pv_is("ID", "Flipper Control")
        self.ca.assert_that_pv_alarm_is("ID", self.ca.Alarms.NONE)

    @parameterized.expand(["ANALYSER", "POLARISER"])
    def test_GIVEN_amplitude_is_set_THEN_amplitude_can_be_read_back(self, flipper):
        for val in [0., 0.12, 5000.5]:
            self.ca.assert_setting_setpoint_sets_readback(val, readback_pv="{}:AMPLITUDE".format(flipper))

    @parameterized.expand(["ANALYSER", "POLARISER"])
    def test_GIVEN_amplitude_is_set_THEN_amplitude_can_be_read_back(self, flipper):
        for val in [0., 0.12, 5000.5]:
            self.ca.assert_setting_setpoint_sets_readback(val, readback_pv="{}:COMPENSATION".format(flipper))
