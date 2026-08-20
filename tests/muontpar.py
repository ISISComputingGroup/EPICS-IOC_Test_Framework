import unittest
from pathlib import PureWindowsPath

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import (
    IOCRegister,
    get_default_ioc_dir,
)
from utils.test_modes import TestModes

ioc_number = 1
DEVICE_PREFIX = "MUONTPAR_01"

test_config_path = PureWindowsPath(__file__).parent.parent / "test_data" / "muontpar"
DEFAULT_INPUT_FILE = "tpar.tpar"
DEFAULT_OUTPUT_FILE = "current.tpar"
IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MUONTPAR"),
        "pv_for_existence": "FILE_DIR",
        "macros": {
            "EDITOR_TPAR_FILE_DIR": str(test_config_path).replace("\\", "\\\\"),
            "TPAR_FILE": DEFAULT_INPUT_FILE,
        },
    },
]


TEST_MODES = [TestModes.RECSIM]
TEST_TPAR = """/   TLOW      THIGH    CYCLE    PROP    INT      DER     ACCUR     WAIT    TMOUT
/ --------   --------  ------  ------  ------  -------  --------   ----    -----
 0001.000   095.000   100.00  003.00  050.00  008.000  0000.400     5.      61. 
 0095.000   145.000   100.00  001.50  070.00  012.000  0000.400     5.      62. 
 0145.000   170.000   100.00  001.50  085.00  014.000  0002.000     5.      63.
 0170.000   250.000   100.00  001.50  250.00  050.000  0002.000     5.      60.
 0250.000   701.000   100.00  001.50  250.00  050.000  0002.000     10.      60.

"""


class MuonTPARTests(unittest.TestCase):
    """
    Tests for the muon tpar IOC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(5, device_prefix=DEVICE_PREFIX, default_wait_time=0.0)

    def test_tpar_dir_populates_file_dir_pv(self):
        self.ca.assert_that_pv_is("FILE_DIR", str(test_config_path))

    def test_tpar_file_contents_match_disk_contents_on_read(self):
        self.ca.assert_that_pv_is("INPUT_FILE", DEFAULT_INPUT_FILE)
        self.ca.assert_that_pv_is("OUTPUT_FILE", DEFAULT_OUTPUT_FILE)
        with open(test_config_path / DEFAULT_OUTPUT_FILE, "rb") as tpar_file:
            self.ca.assert_that_pv_is("LINES_ARRAY:SP", tpar_file.read().decode('utf-8'))

    def test_tpar_editor_writes_tpar_content(self):
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        self.ca.set_pv_value("LINES_ARRAY:SP", TEST_TPAR)
        self.ca.assert_that_pv_is("LINES_ARRAY:SP", TEST_TPAR)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "Yes")
        self.ca.set_pv_value("SAVE_FILE", 1, wait=True)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        with open(test_config_path / DEFAULT_OUTPUT_FILE, "rb") as tpar_file:
            self.assertEqual(TEST_TPAR, tpar_file.read().decode('utf-8'))

    def test_tpar_editor_reset(self):
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        self.ca.set_pv_value("LINES_ARRAY:SP", TEST_TPAR)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "Yes")
        self.ca.set_pv_value("RESET", 1)
        self.ca.assert_that_pv_is("UNSAVED_CHANGES", "No")
        with open(test_config_path / DEFAULT_OUTPUT_FILE, "rb") as tpar_file:
            self.ca.assert_that_pv_is("LINES_ARRAY:SP", tpar_file.read().decode('utf-8'))
