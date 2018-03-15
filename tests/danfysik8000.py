from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

from common_tests.danfysik import DanfysikBase, DEVICE_PREFIX, EMULATOR_NAME
from utils.testing import skip_if_recsim

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
        },
        "emulator": EMULATOR_NAME,
        "emulator_protocol": "model8000",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


INTERLOCKS = {
    "fw_diode_overtemp": "ILK:FWDI",
    "user1": "ILK:USER1",
    "user2": "ILK:USER2",
    "user3": "ILK:USER3",
    "user4": "ILK:USER4",
    "user5": "ILK:USER5",
    "user6": "ILK:USER6",
    "low_water_flow": "ILK:WATER",
    "door_open": "ILK:DOOR",
    "diode_heatsink": "ILK:HSDI",
    "chassis_overtemp": "ILK:CHASSIS",
    "igbt_heatsink_overtemp": "ILK:IGBTHS",
    "hf_diode_overtemp": "ILK:HFDI",
    "switch_reg_ddct_fail": "ILK:DCCT",
    "switch_reg_supply_fail": "ILK:REGSUP",
    "igbt_driver_fail": "ILK:IGBT",
    "overcurrent": "ILK:OVERC",
}


class Danfysik8000Tests(DanfysikBase):
    """
    Tests for danfysik model 8000. Tests inherited from DanfysikBase.
    """
    def test_GIVEN_ioc_THEN_model_is_set_correctly(self):
        self.ca.assert_that_pv_is("DEV_TYPE", "8000")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_interlocks_set_to_active_via_backdoor_THEN_interlock_pvs_update(self):
        for ilk_name, ilk_pv in INTERLOCKS.items():
            self.ca.assert_that_pv_is(ilk_pv, "OK")
            self._lewis.backdoor_command(["device", "enable_interlock", ilk_name])
            self.ca.assert_that_pv_is(ilk_pv, "Interlock")
            self._lewis.backdoor_command(["device", "disable_interlock", ilk_name])
            self.ca.assert_that_pv_is(ilk_pv, "OK")
