import unittest

from common_tests.tpgx6x import TpgBase
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes


DEVICE_PREFIX = "TPG36X_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TPG36X"),
        "emulator": "tpgx6x",
        "lewis_protocol": "tpg36x",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tpg36xTests(TpgBase, unittest.TestCase):
    def get_prefix(self):
        return DEVICE_PREFIX
