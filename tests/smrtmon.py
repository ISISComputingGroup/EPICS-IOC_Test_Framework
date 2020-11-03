import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

IOC_NAME = "SMRTMON"
IOC_PREFIX = "SMRTMON_01"

IOCS = [
    {
        "name": "SMRTMON_01",
        "directory": get_default_ioc_dir(IOC_NAME),
        "custom_prefix": IOC_PREFIX,
        "pv_for_existence": "HEARTBEAT",
        "macros": {
        },
        "emulator": "smrtmon"
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

MAGNET_STATUS = {
    0: "",
    1: "Magnet Is At Room Temperature",
    2: "Magnet Is Cooling Down",
    3: "Magnet Is At Operating Temperature",
    4: "A Fault Has Occurred"
}


class SmrtmonTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("smrtmon", IOC_PREFIX)
        self.ca = ChannelAccess(device_prefix=IOC_PREFIX)

    def _write_stat(self, expected_stat):
        self._lewis.backdoor_set_on_device("stat1", expected_stat)
        self._ioc.set_simulated_value("SIM:STAT", expected_stat)

    def _write_oplms(self, expected_oplm):
        self._lewis.backdoor_set_on_device("oplm1", expected_oplm)
        self._ioc.set_simulated_value("SIM:OPLM", expected_oplm)

    def _write_lims(self, expected_lims):
        self._lewis.backdoor_set_on_device("lims1", expected_lims)
        self._ioc.set_simulated_value("SIM:LIMS", expected_lims)

    def test_WHEN_stat_changes_THEN_pv_also_changes(self):
        stat = 1
        self._write_stat(stat)
        self.ca.assert_that_pv_is("STAT", stat)

    def test_WHEN_oplm_changes_THEN_pv_also_changes(self):
        oplm = 1
        self._write_oplms(oplm)
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
        stat = 123456789
        self._write_stat(stat)
        self.ca.assert_that_pv_is("STATBUFFER", stat)

    def test_WHEN_oplm_changes_THEN_buffer_changes(self):
        oplm = 123456789
        self._write_oplms(oplm)
        self.ca.assert_that_pv_is("OPLMBUFFER", oplm)

    def test_WHEN_lims_changes_THEN_buffer_changes(self):
        lims = 123456789
        self._write_lims(lims)
        self.ca.assert_that_pv_is("LIMSBUFFER", lims)

    def test_WHEN_stat_changes_THEN_pvs_change(self):
        pass

    def test_WHEN_oplm_changes_THEN_pvs_change(self):
        pass

    def test_WHEN_lims_changes_THEN_pvs_change(self):
        pass
