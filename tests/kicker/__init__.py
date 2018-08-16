from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

from tests import KickerVoltageTests, KickerCurrentTests

DEVICE_PREFIX = "KICKER_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KICKER"),
        "macros": {},
    },
]

TEST_MODES = [TestModes.RECSIM]
