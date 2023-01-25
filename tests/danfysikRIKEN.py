from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from tests.danfysik8500 import Danfysik8500Tests, DEVICE_PREFIX, EMULATOR_NAME

MAX_RAW_SETPOINT = 1000000
MIN_RAW_SETPOINT = MAX_RAW_SETPOINT * (-1)

DEVICE_ADDRESS = 75

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "DEV_TYPE": "8500",
            "PROTO_OVERRIDE": "RIKEN",       # use modified protocol file for RB2 PSU
            "CALIBRATED": "0",
            "FACTOR_READ_I": "1",
            "FACTOR_READ_V": "1",
            "FACTOR_WRITE_I": "1",
            "ADDRESS": DEVICE_ADDRESS,
            "DISABLE_AUTOONOFF": "0",
            "MAX_RAW_SETPOINT": MAX_RAW_SETPOINT,
            "POLARITY": "BIPOLAR",
        },
        "emulator": EMULATOR_NAME,
        "lewis_protocol": "RIKEN",       # use modified protocol file for RB2 PSU
        "ioc_launcher_class": ProcServLauncher,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

USE_SLEW_MACRO = "USE_SLEW"
SLEW_PVs = ["SLEW1", "SLEW2", "SLEWABS"]


class DanfysikRIKENTests(Danfysik8500Tests):
    """
    Tests for danfysik-like PSU on RIKEN (RB2). Tests inherited from Danfysik8500.
    """
    pass


# delete Danfysik class so that unitest does not instantiate and rerun tests
del Danfysik8500Tests
