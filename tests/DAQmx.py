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
    },
]


TEST_MODES = [TestModes.DEVSIM]
BUILD_ARCHITECTURES = [BuildArchitectures._64BIT]


class DAQmxNonMonsterTests(DAQmxTests, unittest.TestCase):
    """
    General tests for the DAQmx.
    """

    def test_WHEN_acquire_called_THEN_data_gathered_and_is_changing(self):
        self.ca.set_pv_value("ACQUIRE", 1)

        def non_zero_data(data):
            return all([d != 0.0 for d in data])

        self.ca.assert_that_pv_value_causes_func_to_return_true("DATA", non_zero_data)
        self.ca.assert_that_pv_value_is_changing("DATA", 1)
