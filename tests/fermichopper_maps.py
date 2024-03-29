import unittest
from utils.test_modes import TestModes
from utils.build_architectures import BuildArchitectures
from utils.ioc_launcher import get_default_ioc_dir
from common_tests.fermichopper import FermichopperBase


DEVICE_PREFIX = "FERMCHOP_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FERMCHOP"),
        "macros": {
            "INST": "maps",
            "MHZ": "18.0",
        },
        "emulator": "fermichopper",
        "lewis_protocol": "fermi_maps",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
# VISA not yet available on 32 bit
BUILD_ARCHITECTURES = [BuildArchitectures._64BIT]


class MapsFermiChopperTests(FermichopperBase, unittest.TestCase):
    """
    All tests inherited from FermiChopperBase
    """

    def _get_device_prefix(self):
        return DEVICE_PREFIX
