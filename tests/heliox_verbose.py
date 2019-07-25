from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from .heliox_concise import HelioxConciseTests as HelioxVerboseTests, HE3POT_COARSE_TIME

DEVICE_PREFIX = "HELIOX_01"
EMULATOR_NAME = "heliox"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HELIOX"),
        "emulator": EMULATOR_NAME,
        "macros": {
            "PROTO": "heliox_v.proto",  # Use verbose protocol for these tests.
            "HE3POT_COARSE_TIME": HE3POT_COARSE_TIME,
        }
    },
]


TEST_MODES = [TestModes.DEVSIM]  # Recsim not necessary, tested by main heliox tests, this is just a protocol change.


__all__ = ["HelioxVerboseTests"]
