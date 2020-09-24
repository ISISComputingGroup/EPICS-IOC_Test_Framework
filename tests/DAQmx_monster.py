import unittest
from time import sleep

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP
from utils.emulator_launcher import CommandLineEmulatorLauncher, DEVICE_EMULATOR_PATH, DAQMxEmulatorLauncher
from utils.testing import get_running_lewis_and_ioc, assert_log_messages

import os


# Device prefix
DEVICE_PREFIX = "DAQMXTEST"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "support", "DAQmxBase", "master", "iocBoot",  "iocDAQmx"),
        "emulator": DEVICE_PREFIX,
        "emulator_launcher_class": DAQMxEmulatorLauncher,
        "pv_for_existence": "ACQUIRE",
        "macros": {
            "DAQPOSTIOCINITCMD": "DAQmxStart('myport1')",
            "DAQMODE": "MONSTER TerminalDiff N=1 F=1000"
        },
        "started_text": "DAQmxStart",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class DAQmxMonsterTests(unittest.TestCase):
    """
    General tests for the DAQmx.
    """
    def setUp(self):
        self.emulator, self._ioc = get_running_lewis_and_ioc(DEVICE_PREFIX, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_emulator_disconnected_THEN_data_in_alarm_and_valid_on_reconnect(self):
        self.ca.assert_that_pv_alarm_is_not("DATA", ChannelAccess.Alarms.INVALID)
        self.emulator.disconnect_device()
        self.ca.assert_that_pv_alarm_is("DATA", ChannelAccess.Alarms.INVALID)

        # Check we don't get excessive numbers of messages if we stay disconnected for 15s (up to 15 messages seems
        # reasonable - 1 per second on average)
        with assert_log_messages(self._ioc, number_of_messages=15):
            sleep(15)
            # Double-check we are still in alarm
            self.ca.assert_that_pv_alarm_is("DATA", ChannelAccess.Alarms.INVALID)

        self.emulator.reconnect_device()
        self.ca.assert_that_pv_alarm_is_not("DATA", ChannelAccess.Alarms.INVALID, timeout=5)
        self.ca.assert_that_pv_value_is_changing("DATA", 1)


