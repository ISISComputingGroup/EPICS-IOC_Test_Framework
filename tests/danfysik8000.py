import unittest
from time import sleep

from utils.channel_access import ChannelAccess

from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir

from common_tests.danfysik import DanfysikCommon, DEVICE_PREFIX, EMULATOR_NAME
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
            self.ca.assert_that_pv_is(ilk_pv, "OK")
            self._lewis.backdoor_command(["device", "enable_interlock", ilk_name])
            self.ca.assert_that_pv_is(ilk_pv, "Interlock")
            self._lewis.backdoor_command(["device", "disable_interlock", ilk_name])
            self.ca.assert_that_pv_is(ilk_pv, "OK")

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_voltage_pv_checked_THEN_pv_in_alarm(self):
        sleep(5)
        self._lewis.backdoor_set_on_device('comms_initialized', False)
        self._lewis.backdoor_set_on_device('device_available', False)
        sleep(10)
        self.ca.assert_that_pv_alarm_is('VOLT', ChannelAccess.Alarms.INVALID)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_current_pv_checked_THEN_pv_in_alarm(self):
        sleep(5)
        self._lewis.backdoor_set_on_device('comms_initialized', False)
        self._lewis.backdoor_set_on_device('device_available', False)
        sleep(10)
        self.ca.assert_that_pv_alarm_is('CURR', ChannelAccess.Alarms.INVALID)
