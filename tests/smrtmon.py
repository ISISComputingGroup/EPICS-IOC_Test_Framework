import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

SET_OPLM = "set_oplm"
SET_LIMS = "set_lims"
SET_STAT = "set_stat"

IOC_NAME = "SMRTMON"
IOC_PREFIX = "SMRTMON_01"
IOCS = [
    {
        "name": IOC_PREFIX,
        "directory": get_default_ioc_dir(IOC_NAME),
        "macros": {},
        "emulator": "smrtmon"
    },
]
# All of these have their own PVs plus PVNAME:OPLM and PVNAME:LIMS
DEVICE_PVS = ["TEMP1", "TEMP2", "TEMP3", "TEMP4", "TEMP5", "TEMP6", "VOLT1", "VOLT2", "VOLT3"]
DEVICE_LIMS_PVS = [pv + ":LIMS" for pv in DEVICE_PVS]
DEVICE_OPLM_PVS = [pv + ":OPLM" for pv in DEVICE_PVS]
MAGNET_STATUS_PV_NAME = "MAGNETSTATUS"
STAT_EXTRA_PVS = ["MI", "STATUS"]
TEST_MODES = [TestModes.DEVSIM]

MAGNET_STATUS = {
    0: "",
    1: "At Room Temperature",
    2: "Cooling Down",
    3: "At Operating Temperature",
    4: "A Fault Has Occurred"
}


class SmrtmonTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("smrtmon", IOC_PREFIX)
        self.ca = ChannelAccess(device_prefix=IOC_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset_values")
        self.ca.assert_that_pv_alarm_is_not("STAT", ChannelAccess.Alarms.INVALID)

    @parameterized.expand(MAGNET_STATUS.items())
    def test_WHEN_status_changes_THEN_magnetstatus_enum_is_updated(self, num, status):
        # Check when the STATUS value updates the MAGNETSTATUS enum is updated with the correct string
        self._lewis.backdoor_run_function_on_device(SET_STAT, [10, num])
        self.ca.assert_that_pv_is(MAGNET_STATUS_PV_NAME, status)

    @parameterized.expand(enumerate(DEVICE_PVS + STAT_EXTRA_PVS))
    def test_WHEN_stat_changes_THEN_pvs_change(self, num, pv):
        stat_value = 1.0
        self._lewis.backdoor_run_function_on_device(SET_STAT, [num, stat_value])
        self.ca.assert_that_pv_is(pv, stat_value)

    @parameterized.expand(enumerate(DEVICE_OPLM_PVS))
    def test_WHEN_oplm_changes_THEN_pvs_change(self, num, pv):
        oplm_value = 1.0
        self._lewis.backdoor_run_function_on_device(SET_OPLM, [num, oplm_value])
        self.ca.assert_that_pv_is(pv, oplm_value)

    @parameterized.expand(enumerate(DEVICE_LIMS_PVS))
    def test_WHEN_lims_changes_THEN_pvs_change(self, num, pv):
        lims_value = 1.0
        self._lewis.backdoor_run_function_on_device(SET_LIMS, [num, lims_value])
        self.ca.assert_that_pv_is(pv, lims_value)

    @parameterized.expand(enumerate(DEVICE_PVS + DEVICE_OPLM_PVS + DEVICE_LIMS_PVS + [MAGNET_STATUS_PV_NAME]))
    def test_WHEN_disconnected_THEN_in_alarm(self, _, pv):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is(pv, ChannelAccess.Alarms.INVALID)

    @parameterized.expand(enumerate(DEVICE_PVS))
    def test_GIVEN_oplm_WHEN_stat_greater_than_oplm_THEN_minor_alarm(self, num, pv):
        oplm_value = 123
        stat_value = 124
        lims_value = 125
        self._lewis.backdoor_run_function_on_device(SET_OPLM, [num, oplm_value])
        self._lewis.backdoor_run_function_on_device(SET_LIMS, [num, lims_value])
        self.ca.assert_that_pv_alarm_is(pv, ChannelAccess.Alarms.NONE)
        self._lewis.backdoor_run_function_on_device(SET_STAT, [num, stat_value])
        self.ca.assert_that_pv_alarm_is(pv, ChannelAccess.Alarms.MINOR)

    @parameterized.expand(enumerate(DEVICE_PVS))
    def test_GIVEN_lims_WHEN_stat_greater_than_lims_THEN_major_alarm(self, num, pv):
        oplm_value = 123
        stat_value = 125
        lims_value = 124
        self._lewis.backdoor_run_function_on_device(SET_OPLM, [num, oplm_value])
        self._lewis.backdoor_run_function_on_device(SET_LIMS, [num, lims_value])
        self.ca.assert_that_pv_alarm_is(pv, ChannelAccess.Alarms.NONE)
        self._lewis.backdoor_run_function_on_device(SET_STAT, [num, stat_value])
        self.ca.assert_that_pv_alarm_is(pv, ChannelAccess.Alarms.MAJOR)
