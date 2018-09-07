from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

DEVICE_PREFIX = "KICKER_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KICKER"),
        "macros": {},
    },
]

TEST_MODES = [TestModes.RECSIM]

# TestCases imported here are the only tests which are run as part of the
# IOC Test Framework because the IOC Test Framework only runs tests at
# the module level.
from test_basic_commands import VoltageTests, CurrentTests
