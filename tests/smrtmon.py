import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

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

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

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

    def _write_stat(self, expected_stat):
        self._lewis.backdoor_set_on_device("stat", expected_stat)
        self._ioc.set_simulated_value("SIM:STAT", expected_stat)

    def _write_oplm(self, expected_oplm):
        self._lewis.backdoor_set_on_device("oplm", expected_oplm)
        self._ioc.set_simulated_value("SIM:OPLM", expected_oplm)

    def _write_lims(self, expected_lims):
        self._lewis.backdoor_set_on_device("lims", expected_lims)
        self._ioc.set_simulated_value("SIM:LIMS", expected_lims)

    def test_WHEN_stat_changes_THEN_pv_also_changes(self):
        stat = 1
        self._write_stat(stat)
        self.ca.assert_that_pv_is("STAT", stat)

    def test_WHEN_oplm_changes_THEN_pv_also_changes(self):
        oplm = 1
        self._write_oplm(oplm)
        self.ca.assert_that_pv_is("OPLM", oplm)

    def test_WHEN_lims_changes_THEN_pv_also_changes(self):
        lims = 1
        self._write_lims(lims)
        self.ca.assert_that_pv_is("LIMS", lims)

    @parameterized.expand(MAGNET_STATUS.items())
    def test_WHEN_status_changes_THEN_magnetstatus_enum_is_updated(self, num, status):
        # Check when the STATUS value updates the MAGNETSTATUS enum is updated with the correct string
        self.ca.set_pv_value("STATUS", num)
        self.ca.assert_that_pv_is("MAGNETSTATUS", status)

    def test_WHEN_stat_changes_THEN_buffer_changes(self):
        stat = "1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,1,2"
        self._write_stat(stat)
        self.ca.assert_that_pv_is("STATBUFFER", stat)

    def test_WHEN_oplm_changes_THEN_buffer_changes(self):
        oplm = "1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0"
        self._write_oplm(oplm)
        self.ca.assert_that_pv_is("OPLMBUFFER", oplm)

    def test_WHEN_lims_changes_THEN_buffer_changes(self):
        lims = "1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0"
        self._write_lims(lims)
        self.ca.assert_that_pv_is("LIMSBUFFER", lims)

    def test_WHEN_stat_changes_THEN_pvs_change(self):
        # TODO: make this parametrized somehow
        temp = 1.0
        self._write_stat("{},0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1,2".format(str(temp)))
        self.ca.assert_that_pv_is("TEMP1", temp)

    def test_WHEN_oplm_changes_THEN_pvs_change(self):
        oplm = 3
        self._write_oplm("{},0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1,2".format(str(oplm)))
        self.ca.assert_that_pv_is("TEMP1:OPLM", oplm)

    def test_WHEN_lims_changes_THEN_pvs_change(self):
        lims = 4
        self._write_lims("{},0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1,2".format(str(lims)))
        self.ca.assert_that_pv_is("TEMP1:LIMS", lims)
