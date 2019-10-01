import unittest

from common_tests.tpgx6x import TpgBase, ErrorFlags, ErrorStrings
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from parameterized import parameterized


DEVICE_PREFIX = "TPG36X_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TPG36X"),
        "emulator": "tpgx6x",
        "lewis_protocol": "tpg361",
        "macros": {
            "IS361": "Y"
        }
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tpg361Tests(TpgBase, unittest.TestCase):

    def get_prefix(self):
        return DEVICE_PREFIX

    def setUp(self):
        TpgBase.setUp(self)
        self.channels = 1
