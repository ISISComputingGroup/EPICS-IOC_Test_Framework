import unittest

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher

from common_tests.danfysik import DanfysikCommon, DEVICE_PREFIX, EMULATOR_NAME, HAS_TRIPPED
from utils.testing import skip_if_recsim

MAX_RAW_SETPOINT = 1000000
MIN_RAW_SETPOINT = MAX_RAW_SETPOINT * (-1)

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("DFKPS"),
        "macros": {
            "DEV_TYPE": "8000",
            "CALIBRATED": "0",
            "FACTOR_READ_I": "1",
            "FACTOR_READ_V": "1",
            "FACTOR_WRITE_I": "1",
            "DISABLE_AUTOONOFF": "0",
            "MAX_RAW_SETPOINT": MAX_RAW_SETPOINT,
            "POLARITY": "BIPOLAR",
        },
        "emulator": EMULATOR_NAME,
        "lewis_protocol": "model8000",
        "ioc_launcher_class": ProcServLauncher,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


INTERLOCKS = {
    "transistor_fault": "ILK:TRANS",
    "dc_overcurrent": "ILK:DCOC",
    "dc_overload": "ILK:DCOL",
    "reg_mod_fail": "ILK:REGMOD",
    "prereg_fail": "ILK:PREREG",
    "phase_fail": "ILK:PHAS",
    "mps_waterflow_fail": "ILK:MPSWATER",
    "earth_leak_fail": "ILK:EARTHLEAK",
    "thermal_fail": "ILK:THERMAL",
    "mps_overtemperature": "ILK:MPSTEMP",
    "door_switch": "ILK:DOOR",
    "mag_waterflow_fail": "ILK:MAGWATER",
    "mag_overtemp": "ILK:MAGTEMP",
}


class Danfysik8000Tests(DanfysikCommon, unittest.TestCase):
    """
    Tests for danfysik model 8000. Tests inherited from DanfysikBase.
    """
    def test_GIVEN_ioc_THEN_model_is_set_correctly(self):
        self.ca.assert_that_pv_is("DEV_TYPE", "8000")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_interlocks_set_to_active_via_backdoor_THEN_interlock_pvs_update(self):
        for ilk_name, ilk_pv in INTERLOCKS.items():
            self.ca.assert_that_pv_is(ilk_pv, HAS_TRIPPED[False])
            self._lewis.backdoor_command(["device", "enable_interlock", ilk_name])
            self.ca.assert_that_pv_is(ilk_pv, HAS_TRIPPED[True])
            self._lewis.backdoor_command(["device", "disable_interlock", ilk_name])
            self.ca.assert_that_pv_is(ilk_pv, HAS_TRIPPED[False])

    def test_GIVEN_polarity_is_bipolar_WHEN_setting_current_THEN_min_setpoint_is_negative_of_max_setpoint(self):
        self.ca.set_pv_value("CURR:SP", MIN_RAW_SETPOINT * 2)

        self.ca.assert_that_pv_is("RAW:SP", MIN_RAW_SETPOINT)
        self.ca.assert_that_pv_is("RAW", MIN_RAW_SETPOINT)
