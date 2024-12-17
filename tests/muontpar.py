import os
import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import (
    IOCRegister,
    get_default_ioc_dir,
)
from utils.test_modes import TestModes
from utils.testing import ManagerMode

ioc_number = 1
DEVICE_PREFIX = "MUONTPAR_01"

test_config_path = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data", "muontpar")
).replace("\\", "/")


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MUONTPAR"),
        "pv_for_existence": "FILE_DIR",
        "macros": {"EDITOR_TPAR_FILE_DIR": test_config_path},
    },
        {
        # INSTETC is required to control manager mode.
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
    },
]


TEST_MODES = [TestModes.RECSIM]
TEST_TPAR = """
/   TLOW      THIGH    CYCLE    PROP    INT      DER     ACCUR     WAIT    TMOUT
/ --------   --------  ------  ------  ------  -------  --------   ----    -----
 0001.000   095.000   100.00  003.00  050.00  008.000  0000.400     5.      61. 
 0095.000   145.000   100.00  001.50  070.00  012.000  0000.400     5.      62. 
 0145.000   170.000   100.00  001.50  085.00  014.000  0002.000     5.      63.
 0170.000   250.000   100.00  001.50  250.00  050.000  0002.000     5.      60.
 0250.000   701.000   100.00  001.50  250.00  050.000  0002.000     10.      60.

"""
TEST_TPAR_FILENAME = "test_write.tpar"

class MuonTPARTests(unittest.TestCase):
    """
    Tests for the muon tpar IOC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(5, device_prefix=DEVICE_PREFIX, default_wait_time=0.0)
        if os.path.exists(os.path.join(test_config_path, TEST_TPAR_FILENAME)):
            os.remove(os.path.join(test_config_path, TEST_TPAR_FILENAME))

    def test_tpar_dir_populates_file_dir_pv(self):
        self.ca.assert_that_pv_is("FILE_DIR", test_config_path)

    def test_tpar_file_contents_match_disk_contents_on_read(self):
        file_name = "tpar.tpar"
        self.ca.set_pv_value("FILE_NAME:SP", file_name)
        self.ca.assert_that_pv_is("FILE_NAME", file_name)
        self.ca.assert_that_pv_is("NEW_FILE_WARNING", "No")
        with open(os.path.join(test_config_path, file_name), "r") as tpar_file:
            self.ca.assert_that_pv_is("LINES_ARRAY:SP", tpar_file.read())

    def test_tpar_missing_file_gives_warning(self):
        file_name = "tpar.tpar"
        self.ca.set_pv_value("FILE_NAME:SP", file_name)
        self.ca.assert_that_pv_is("NEW_FILE_WARNING", "No")
        self.ca.set_pv_value("FILE_NAME:SP", "missing_file.txt")
        self.ca.assert_that_pv_is("NEW_FILE_WARNING", "Yes")

    def test_tpar_editor_writes_tpar_content(self):
        file_name = TEST_TPAR_FILENAME
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        self.ca.set_pv_value("FILE_NAME:SP", file_name, wait=True)
        self.ca.assert_that_pv_is("NEW_FILE_WARNING", "Yes")
        self.ca.set_pv_value("LINES_ARRAY:SP", TEST_TPAR)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "Yes")
        with ManagerMode(ChannelAccess()):
            self.ca.set_pv_value("SAVE_FILE", 1, wait=True)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        self.ca.assert_that_pv_is("NEW_FILE_WARNING", "No")
        with open(os.path.join(test_config_path, file_name), "r") as tpar_file:
            self.assertEqual(TEST_TPAR, tpar_file.read())

    def test_tpar_editor_reset(self):
        file_name = "tpar.tpar"
        self.ca.set_pv_value("FILE_NAME:SP", file_name, wait=True)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        self.ca.assert_that_pv_is("NEW_FILE_WARNING", "No")
        self.ca.set_pv_value("LINES_ARRAY:SP", TEST_TPAR)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "Yes")
        self.ca.set_pv_value("RESET", 1)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        with open(os.path.join(test_config_path, file_name), "r") as tpar_file:
            self.ca.assert_that_pv_is("LINES_ARRAY:SP", tpar_file.read())

