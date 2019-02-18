import unittest
import os

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import ProcServLauncher
from utils.ioc_launcher import IOCRegister
from utils.testing import assert_log_messages
from utils.test_modes import TestModes

DEVICE_PREFIX = "SIMPLE"

EPICS_ROOT = os.getenv("EPICS_KIT_ROOT")

IOCS = [
    {
        "LAUNCHER": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": os.path.realpath(os.path.join(EPICS_ROOT, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple")),
        "macros": {},
    },
]


TEST_MODES = [TestModes.RECSIM, ]


class SimpleTests(unittest.TestCase):
    """
    Tests for the Simple IOC
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        self.set_auto_restart_to_true()

    def set_auto_restart_to_true(self):
        if not self._ioc.autorestart:
            self._ioc.toggle_autorestart()

    def test_GIVEN_running_ioc_in_auto_restart_mode_WHEN_ioc_crashes_THEN_ioc_reboots(self):
        # GIVEN
        self.set_auto_restart_to_true()
        self.ca.assert_that_pv_exists("DISABLE")

        # WHEN
        with assert_log_messages(self._ioc, in_time=30, must_contain="dbLoadRecords"):
            self.ca.set_pv_value("CRASHVALUE", "1")

        # THEN
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)


