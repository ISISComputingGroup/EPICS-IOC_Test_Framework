import unittest

from common_tests.tpgx6x import TpgBase
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "TPG26X_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TPG26X"),
        "emulator": "tpgx6x",
        "lewis_protocol": "tpg26x",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tpg26xTests(TpgBase, unittest.TestCase):
    def get_prefix(self):
        return DEVICE_PREFIX
