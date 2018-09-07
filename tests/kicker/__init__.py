from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes

# Set up the IOC in the __init__.py file.

DEVICE_PREFIX = "KICKER_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KICKER"),
        "macros": {},
    },
]

TEST_MODES = [TestModes.RECSIM]

# Import all the tests to be run as part of the IOC test framework.
# These are the only tests which are run because the IOC test
# framework only runs tests in each python module and not submodules.

from test_basic_commands import VoltageTests, CurrentTests
