from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "HELIOX_01"
EMULATOR_NAME = "heliox"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HELIOX"),
        "emulator": EMULATOR_NAME,
        "macros": {
            "PROTO": "heliox_v.proto"  # Use verbose protocol for these tests.
        }
    },
]


TEST_MODES = [TestModes.DEVSIM]  # Recsim not necessary, tested by main heliox tests, this is just a protocol change.


from .heliox_concise import HelioxConciseTests as HelioxVerboseTests

__all__ = ["HelioxVerboseTests"]
