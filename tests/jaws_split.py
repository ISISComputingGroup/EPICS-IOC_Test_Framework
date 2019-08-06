import os

from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes

MTR_01 = "GALIL_01"
MTR_02 = "GALIL_02"

# Tests will fail if JAWS support module is not up to date and built
test_path = os.path.realpath(
    os.path.join(os.getenv("EPICS_KIT_ROOT"), "support", "jaws", "master", "settings", "jaws_full_split"))

IOCS = [
    {
        "name": MTR_01,
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "01",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
    {
        "name": MTR_02,
        "directory": get_default_ioc_dir("GALIL", iocnum=2),
        "pv_for_existence": "AXIS1",
        "macros": {
            "MTRCTRL": "02",
            "GALILCONFIGDIR": test_path.replace("\\", "/"),
        },
    },
]

TEST_MODES = [TestModes.DEVSIM]

# PV names for GALIL motors


from .jaws import JawsTests as SplitJawsTests

mtr_north = "MOT:MTR0101"
mtr_south = "MOT:MTR0102"
mtr_east = "MOT:MTR0201"
mtr_west = "MOT:MTR0202"

SplitJawsTests.MTR_NORTH = mtr_north
SplitJawsTests.MTR_SOUTH = mtr_south
SplitJawsTests.MTR_EAST = mtr_east
SplitJawsTests.MTR_WEST = mtr_west
SplitJawsTests.UNDERLYING_MTRS = [mtr_north, mtr_south, mtr_east, mtr_west]

__all__ = ["SplitJawsTests"]
