import os
import time
import unittest
from contextlib import contextmanager
from math import radians, tan

from genie_python.channel_access_exceptions import WriteAccessException
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import (
    IOCRegister,
    ProcServLauncher,
    get_default_ioc_dir,
)
from utils.test_modes import TestModes
from utils.testing import ManagerMode, parameterized_list, unstable_test

ioc_number = 1
DEVICE_PREFIX = "MUONTPAR_01"

test_config_path = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data", "muontpar")
)


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MUONTPAR"),
        "pv_for_existence": "FILE_DIR",
        "macros": {"EDITOR_TPAR_FILE_DIR": test_config_path.replace("\\", "\\\\") + "\\"},
    },
]


TEST_MODES = [TestModes.RECSIM]


class MuonTPARTests(unittest.TestCase):
    """
    Tests for the muon tpar IOC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(5, device_prefix=DEVICE_PREFIX, default_wait_time=0.0)

    def test_tpar_dir_populates_file_dir_pv(self):
        self.ca.assert_that_pv_is("FILE_DIR", test_config_path + "\\") 
        
    def test_tpar_file_contents_match_disk_contents(self):
        file_name = "tpar.tpar"
        self.ca.set_pv_value("FILE_NAME:SP", file_name)
        with open(os.path.join(test_config_path, file_name), "r") as tpar_file:
            self.ca.assert_that_pv_is("LINES_ARRAY:SP", tpar_file.read() + "\n")