import time
import unittest

from common_tests.instron_base import InstronBase
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

# Device prefix
DEVICE_PREFIX = "INSTRONA_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("INSTRONA"),
        "macros": {},
        "emulator": "instron_stress_rig",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class InstronTests(InstronBase, unittest.TestCase):
    def setUp(self):
        super().setUp()

        # Arby control does not need to refresh the watchdog. Simulate this for tests.
        self._lewis.backdoor_set_on_device("watchdog_refresh_time", time.time() + 1000000000)

    def get_prefix(self):
        return DEVICE_PREFIX
