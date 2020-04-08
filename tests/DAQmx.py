import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import EPICS_TOP
from utils.emulator_launcher import CommandLineEmulatorLauncher, DEVICE_EMULATOR_PATH
from utils.testing import get_running_lewis_and_ioc

import os


class DAQMxEmulatorLauncher(CommandLineEmulatorLauncher):
    def __init__(self, device, var_dir, port, options):
        labview_scripts_dir = os.path.join(DEVICE_EMULATOR_PATH, "other_emulators", "DAQmx")
        self.start_command = os.path.join(labview_scripts_dir, "start_sim.bat")
        self.stop_command = os.path.join(labview_scripts_dir, "stop_sim.bat")
        options["emulator_command_line"] = self.start_command
        options["emulator_wait_to_finish"] = True
        super(DAQMxEmulatorLauncher, self).__init__(device, var_dir, port, options)

    def _close(self):
        self.disconnect_device()
        super(DAQMxEmulatorLauncher, self)._close()

    def disconnect_device(self):
        self._call_command_line(self.stop_command)

    def reconnect_device(self):
        self._call_command_line(self.start_command)


# Device prefix
DEVICE_PREFIX = "DAQMXTEST"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "support", "DAQmxBase", "master", "iocBoot",  "iocDAQmx"),
        "emulator": DEVICE_PREFIX,
        "emulator_launcher_class": DAQMxEmulatorLauncher,
        "pv_for_existence": "ACQUIRE",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class DAQmxTests(unittest.TestCase):
    """
    General tests for the DAQmx.
    """
    def setUp(self):
        self.emulator, self._ioc = get_running_lewis_and_ioc(DEVICE_PREFIX, DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_acquire_called_THEN_data_gathered_and_is_changing(self):
        self.ca.set_pv_value("ACQUIRE", 1)

        def non_zero_data(data):
            return all([d != 0.0 for d in data])
        self.ca.assert_that_pv_value_causes_func_to_return_true("DATA", non_zero_data)
        self.ca.assert_that_pv_value_is_changing("DATA", 1)

    def test_WHEN_emulator_disconnected_THEN_data_in_alarm_and_valid_on_reconnect(self):
        self.ca.assert_that_pv_alarm_is_not("DATA", ChannelAccess.Alarms.INVALID)
        self.emulator.disconnect_device()
        self.ca.assert_that_pv_alarm_is("DATA", ChannelAccess.Alarms.INVALID)

        self.emulator.reconnect_device()
        self.ca.assert_that_pv_alarm_is_not("DATA", ChannelAccess.Alarms.INVALID, timeout=5)
        self.ca.assert_that_pv_value_is_changing("DATA", 1)


