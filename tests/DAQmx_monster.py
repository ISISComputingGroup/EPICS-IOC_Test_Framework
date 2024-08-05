import os
import unittest

from common_tests.DAQmx import DEVICE_PREFIX, ICPCONFIGNAME, DAQmxTests
from utils.build_architectures import BuildArchitectures
from utils.emulator_launcher import DAQMxEmulatorLauncher
from utils.ioc_launcher import EPICS_TOP
from utils.test_modes import TestModes

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "icpconfigname": ICPCONFIGNAME,
        "directory": os.path.join(
            EPICS_TOP, "support", "DAQmxBase", "master", "iocBoot", "iocDAQmx"
        ),
        "emulator": DEVICE_PREFIX,
        "emulator_launcher_class": DAQMxEmulatorLauncher,
        "pv_for_existence": "ACQUIRE",
        "macros": {
            "DAQPOSTIOCINITCMD": "DAQmxStart('myport1')",
            "DAQMODE": "MONSTER TerminalDiff N=1 F=1000",
        },
        "started_text": "DAQmxStart",
    },
]


TEST_MODES = [TestModes.DEVSIM]
BUILD_ARCHITECTURES = [BuildArchitectures._64BIT]


class DAQmxMonsterTests(DAQmxTests, unittest.TestCase):
    """
    Test all DAQMx tests using monster mode.
    """

    pass
