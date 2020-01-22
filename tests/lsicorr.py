import os
import unittest
import time
from contextlib import contextmanager
from math import tan, radians, cos

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, EPICS_TOP, PythonIOCLauncher
from utils.test_modes import TestModes
from utils.testing import ManagerMode
from utils.testing import unstable_test

DEVICE_PREFIX = "LSI"

LSICORR_PATH = os.path.join(EPICS_TOP, "support", "lsicorr", "master")
IOCS = [
    {
        "ioc_launcher_class": PythonIOCLauncher,
        "name": DEVICE_PREFIX,
        "directory": LSICORR_PATH,
        "python_script_commandline": [os.path.join(LSICORR_PATH, "LSi_Correlator.py"), "--pv_prefix", "TE:NDW1836:"],
        "started_text": "IOC started",
        "pv_for_existence": "MEASUREMENTDURATION",
        "python_version": 3,
        "macros": {
        }
    }

]


TEST_MODES = [TestModes.DEVSIM]


class LSITests(unittest.TestCase):
    """
    Tests for LSi Correlator
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("LSI")
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)

    def test_GIVEN_setting_pv_WHEN_pv_written_to_THEN_new_value_read_back(self):
        pv_name = "MEASUREMENTDURATION"
        pv_value = 1000

        self.ca.set_pv_value(pv_name, pv_value)
        self.ca.assert_that_pv_is_number(pv_name, pv_value)

    def test_GIVEN_setting_pv_WHEN_pv_written_to_with_invalid_value_THEN_value_not_updated(self):
        pv_name = "MEASUREMENTDURATION"
        original_value = self.ca.get_pv_value(pv_name)

        self.ca.set_pv_value(pv_name, -1)
        self.ca.assert_that_pv_is_number(pv_name, original_value)

    def test_GIVEN_integer_device_setting_WHEN_pv_written_to_with_a_float_THEN_value_is_rounded_before_setting(self):
        pv_name = "MEASUREMENTDURATION"
        new_value = 12.3

        self.ca.set_pv_value(pv_name, new_value)
        self.ca.assert_that_pv_is_number(pv_name, 12)
