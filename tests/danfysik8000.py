from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

from common_tests.danfysik import DanfysikBase, DEVICE_PREFIX, EMULATOR_NAME

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "DEV_TYPE": "8000",
        },
        "emulator": EMULATOR_NAME,
        "emulator_protocol": "model8000",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Danfysik8000Tests(DanfysikBase):
    """
    Tests for danfysik model 8000. Tests inherited from DanfysikBase.
    """
