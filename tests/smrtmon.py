import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

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

    # @parameterized.expand(MAGNET_STATUS.items())
    # def test_WHEN_status_changes_THEN_magnetstatus_enum_is_updated(self, num, status):
    #     # Check when the STATUS value updates the MAGNETSTATUS enum is updated with the correct string
    #     self.ca.set_pv_value("STATUS", num)
    #     self.ca.assert_that_pv_is("MAGNETSTATUS", status)

    @parameterized.expand(enumerate(DEVICE_PVS + STAT_EXTRA_PVS))
    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_WHEN_stat_changes_THEN_pvs_change(self, num, pv):
        stat_value = 1.0
        self._lewis.backdoor_command(["device", "set_stat", str(num), str(stat_value)])
        self.ca.assert_that_pv_is(pv, stat_value)

    @parameterized.expand(enumerate([pv + ":OPLM" for pv in DEVICE_PVS]))
    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_WHEN_oplm_changes_THEN_pvs_change(self, num, pv):
        oplm_value = 1.0
        self._lewis.backdoor_command(["device", "set_oplm", str(num), str(oplm_value)])
        self.ca.assert_that_pv_is(pv, oplm_value)

    @parameterized.expand(enumerate([pv + ":LIMS" for pv in DEVICE_PVS]))
    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_WHEN_lims_changes_THEN_pvs_change(self, num, pv):
        lims_value = 1.0
        self._lewis.backdoor_command(["device", "set_lims", str(num), str(lims_value)])
        self.ca.assert_that_pv_is(pv, lims_value)
