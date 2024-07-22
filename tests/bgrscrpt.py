import unittest
import os

from utils.ioc_launcher import IOCRegister, ProcServLauncher, get_default_ioc_dir
from utils.test_modes import TestModes


DEVICE_PREFIX = "BGRSCRPT_01"
IOC_DIR = get_default_ioc_dir("BGRSCRPT")
SCRIPT_PATH = os.path.join(
    os.getenv("EPICS_KIT_ROOT"), "ioc", "master", "BGRSCRPT", "settings", "bgrscrpt_script.py"
)
TEMP_DIR = os.path.join("C:\\", "Instrument", "Var", "tmp", "BGRSCRPT_01_test_dir")

IOCS = [
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": IOC_DIR,
        "started_text": "IOC started",
        "pv_for_existence": None,
        "macros": {"SCRIPT_PATH": SCRIPT_PATH},
    }
]


TEST_MODES = [TestModes.DEVSIM]


class BgrscrptTests(unittest.TestCase):
    """
    Tests for the BGRSCRPT IOC.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running("BGRSCRPT_01")

    def tearDown(self):
        if os.path.isdir(TEMP_DIR):
            os.rmdir(TEMP_DIR)

    def test_WHEN_script_from_path_macro_called_THEN_temp_directory_created(self):
        assert os.path.isdir(TEMP_DIR)
