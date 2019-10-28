import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "ICEFRDGE_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("ICEFRDGE"),
        "macros": {},
        "emulator": "icefrdge",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

VTI_TEMP_SUFFIXES = [1, 2, 3, 4]


class IceFridgeTests(unittest.TestCase):
    """
    Tests for the IceFrdge IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(IOCS[0]["emulator"], DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_auto_setpoint_THEN_set_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "AUTO:TEMP:SP:RBV", "AUTO:TEMP:SP")

    def test_WHEN_auto_setpoint_THEN_temperature_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "AUTO:TEMP", "AUTO:TEMP:SP")

    def test_WHEN_manual_setpoint_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "MANUAL:TEMP:SP:RBV", "MANUAL:TEMP:SP")

    def test_WHEN_manual_setpoint_THEN_temperature_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "MANUAL:TEMP", "MANUAL:TEMP:SP")

    @parameterized.expand(parameterized_list(VTI_TEMP_SUFFIXES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_VTI_temp_set_backdoor_THEN_ioc_read_correctly(self, _, temp_num):
        self._lewis.backdoor_set_on_device("vti_temp{}".format(temp_num), 3.6)
        self.ca.assert_that_pv_is_number("VTI:TEMP{}".format(temp_num), 3.6, 0.001)

    def test_WHEN_vti_loop1_setpoint_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(3.6, "VTI:LOOP1:TSET", "VTI:LOOP1:TSET:SP")

    def test_WHEN_vti_loop1_proportional_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(3.6, "VTI:LOOP1:P", "VTI:LOOP1:P:SP")

    def test_WHEN_vti_loop1_integral_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(3.6, "VTI:LOOP1:I", "VTI:LOOP1:I:SP")

    def test_WHEN_vti_loop1_derivative_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(3.6, "VTI:LOOP1:D", "VTI:LOOP1:D:SP")

    def test_WHEN_vti_loop1_ramp_rate_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(3.6, "VTI:LOOP1:RAMPRATE", "VTI:LOOP1:RAMPRATE:SP")

    def test_WHEN_vti_loop2_setpoint_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(2, "VTI:LOOP2:TSET", "VTI:LOOP2:TSET:SP")

    def test_WHEN_vti_loop2_proportional_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(2, "VTI:LOOP2:P", "VTI:LOOP2:P:SP")

    def test_WHEN_vti_loop2_integral_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(2, "VTI:LOOP2:I", "VTI:LOOP2:I:SP")

    def test_WHEN_vti_loop2_derivative_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(2, "VTI:LOOP2:D", "VTI:LOOP2:D:SP")

    def test_WHEN_vti_loop2_ramp_rate_THEN_readback_identical(self):
        self.ca.assert_setting_setpoint_sets_readback(2, "VTI:LOOP2:RAMPRATE", "VTI:LOOP2:RAMPRATE:SP")

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_MC_Cernox_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("lakeshore_mc_cernox", 1.6)
        self.ca.assert_that_pv_is_number("LS:MC:CERNOX", 1.6, 0.001)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_Lakeshore_MC_RuO_set_backdoor_THEN_ioc_read_correctly(self):
        self._lewis.backdoor_set_on_device("lakeshore_mc_ruo", 1.7)
        self.ca.assert_that_pv_is_number("LS:MC:RUO", 1.7, 0.001)