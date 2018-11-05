import unittest

import time
from unittest import skip

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_devsim, skip_if_recsim

# Prefix for addressing PVs on this device
PREFIX = "RKNPS_01"
ADR1 = "001"
ID1 = "RQ1"
ADR2 = "002"
ID2 = "RB1"
CLEAR_STATUS = "."*24
IDS = [ID1, ID2]


IOCS = [
    {
        "name": PREFIX,
        "directory": get_default_ioc_dir("RKNPS"),
        "macros": {
            "CHAIN1_ID1": ID1,
            "CHAIN1_ADR1": ADR1,

            "CHAIN1_ID2": ID2,
            "CHAIN1_ADR2": ADR2,
        },
        "emulator": "rknps",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class RknpsTests(unittest.TestCase):
    """
    Tests for the RIKEN Multidrop Danfysik Power Supplies.
    """

    # Runs before every test.
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("rknps", PREFIX)
        self.ca = ChannelAccess()
        self.ca.assert_that_pv_exists("{0}:{1}:ADDRESS".format(PREFIX, ID1), timeout=30)

    def _activate_interlocks(self):
        """
        Activate both interlocks in the emulator.
        """
        if IOCRegister.uses_rec_sim:
            for IDN in IDS:
                self._ioc.set_simulated_value("{}:SIM:STATUS".format(IDN), ".........!..............")
        else:
            self._lewis.backdoor_set_on_device("set_all_interlocks", True)

    def _disable_interlocks(self):
        """
        Deactivate both interlocks in the emulator.
        """
        if IOCRegister.uses_rec_sim:
            for IDN in IDS:
                self._ioc.set_simulated_value("{}:SIM:STATUS".format(IDN), CLEAR_STATUS)
        else:
            self._lewis.backdoor_set_on_device("set_all_interlocks", False)

    def test_WHEN_intelocks_are_active_THEN_ilk_is_Interlocked(self):
        self._activate_interlocks()
        for IDN in IDS:
            self.ca.assert_that_pv_is("{0}:{1}:ILK".format(PREFIX, IDN), "Interlock")

    def test_WHEN_intelocks_are_inactive_THEN_ilk_is_not_Interlocked(self):
        self._disable_interlocks()
        for IDN in IDS:
            self.ca.assert_that_pv_is("{0}:{1}:ILK".format(PREFIX, IDN), "OK")

    @skip_if_recsim("In rec sim this test fails as recsim does not set any of the related values "
                    "which are set by the emulator")
    def test_WHEN_reset_is_sent_THEN_readbacks_and_power_are_off(self):
        for IDN in IDS:
            self.ca.set_pv_value("{0}:{1}:RESET".format(PREFIX, IDN), 1)
            self.ca.assert_that_pv_is("{0}:{1}:POWER".format(PREFIX, IDN), "Off")
            self.ca.assert_that_pv_is("{0}:{1}:CURR".format(PREFIX, IDN), 0)
            self.ca.assert_that_pv_is("{0}:{1}:VOLT".format(PREFIX, IDN), 0)

    @skip_if_recsim("In rec sim this test fails as there is no link between the status and power")
    def test_GIVEN_emulator_in_use_WHEN_power_is_turned_on_THEN_value_is_as_expected(self):
        for IDN in IDS:
            self.ca.assert_setting_setpoint_sets_readback(1, "{0}:{1}:POWER".format(PREFIX, IDN),
                                                          "{0}:{1}:POWER:SP".format(PREFIX, IDN), "On")

    @skip_if_recsim("In rec sim this test fails as there is no link between the status and power")
    def test_GIVEN_emulator_in_use_WHEN_power_is_turned_off_THEN_value_is_as_expected(self):
        for IDN in IDS:
            self.ca.assert_setting_setpoint_sets_readback(0, "{0}:{1}:POWER".format(PREFIX, IDN),
                                                          "{0}:{1}:POWER:SP".format(PREFIX, IDN), "Off")

    @skip("In dev sim this test fails as the status is maintained by the emulator. In recsim it is hard to implement.")
    def test_GIVEN_emulator_not_in_use_WHEN_power_is_turned_on_THEN_value_is_as_expected(self):
        for IDN in IDS:
            self.ca.assert_setting_setpoint_sets_readback("........................", "{0}:{1}:POWER".format(PREFIX, IDN),
                                                          "{0}:{1}:SIM:STATUS".format(PREFIX, IDN), "On")

    @skip_if_devsim("In dev sim this test fails as the status is maintained by the emulator")
    def test_GIVEN_emulator_not_in_use_WHEN_power_is_turned_off_THEN_value_is_as_expected(self):
        for IDN in IDS:
            self.ca.assert_setting_setpoint_sets_readback("!.......................",
                                                          "{0}:{1}:POWER".format(PREFIX, IDN),
                                                          "{0}:{1}:SIM:STATUS".format(PREFIX, IDN), "Off")

    def test_WHEN_polarity_is_positive_THEN_value_is_as_expected(self):
        for IDN in IDS:
            self.ca.assert_setting_setpoint_sets_readback(0, "{0}:{1}:POL".format(PREFIX, IDN),
                                                          "{0}:{1}:POL:SP".format(PREFIX, IDN), "+")

    def test_WHEN_polarity_is_negative_THEN_value_is_as_expected(self):
        for IDN in IDS:
            self.ca.assert_setting_setpoint_sets_readback(1, "{0}:{1}:POL".format(PREFIX, IDN),
                                                          "{0}:{1}:POL:SP".format(PREFIX, IDN), "-")

    @skip_if_recsim("In rec sim this test fails as it requires a lewis backdoor command")
    def test_GIVEN_emulator_in_use_WHEN_voltage_is_read_THEN_value_is_as_expected(self):
        expected_value = 22
        self._lewis.backdoor_set_on_device("set_all_volt_values", expected_value)
        for IDN in IDS:
            self.ca.assert_that_pv_is("{0}:{1}:VOLT".format(PREFIX, IDN), expected_value)

    @skip_if_devsim("In dev sim this test fails as the simulated records are not used")
    def test_GIVEN_emulator_not_in_use_WHEN_voltage_is_read_THEN_value_is_as_expected(self):
        expected_value = 12
        for IDN in IDS:
            self.ca.set_pv_value("{0}:{1}:SIM:VOLT".format(PREFIX, IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:{1}:VOLT".format(PREFIX, IDN), expected_value)

    @skip_if_recsim("In rec sim this test fails as the changes are not propagated to all appropriate PVs")
    def test_GIVEN_a_positive_value_and_emulator_in_use_WHEN_current_is_set_THEN_values_are_as_expected(self):
        expected_value = 480
        for IDN in IDS:
            self.ca.set_pv_value("{0}:{1}:CURR:SP".format(PREFIX, IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:{1}:CURR".format(PREFIX, IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:{1}:RA".format(PREFIX, IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:{1}:POL".format(PREFIX, IDN), "+")

    @skip_if_recsim("In rec sim this test fails as the changes are not propagated to all appropriate PVs")
    def test_GIVEN_a_negative_value_and_emulator_in_use_WHEN_current_is_set_THEN_values_are_as_expected(self):
        expected_value = -123
        for IDN in IDS:
            self.ca.set_pv_value("{0}:{1}:CURR:SP".format(PREFIX, IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:{1}:CURR".format(PREFIX, IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:{1}:RA".format(PREFIX, IDN), abs(expected_value))
            self.ca.assert_that_pv_is("{0}:{1}:POL".format(PREFIX, IDN), "-")

    @skip_if_devsim("In dev sim this test fails as the emulator "
                    "handles the difference in values between write and read")
    def test_GIVEN_a_positive_value_and_emulator_not_in_use_WHEN_current_is_set_THEN_values_are_as_expected(self):
        set_value = 480
        return_value = set_value*1000
        for IDN in IDS:
            self.ca.set_pv_value("{0}:{1}:CURR:SP".format(PREFIX, IDN), set_value)
            self.ca.assert_that_pv_is("{0}:{1}:CURR".format(PREFIX, IDN), return_value)
            self.ca.assert_that_pv_is("{0}:{1}:RA".format(PREFIX, IDN), return_value)

    @skip_if_devsim("In dev sim this test fails as the emulator "
                    "handles the difference in values between write and read")
    def test_GIVEN_a_negative_value_and_emulator_not_in_use_WHEN_current_is_set_THEN_values_are_as_expected(self):
        set_value = -123
        return_value = set_value*1000
        for IDN in IDS:
            self.ca.set_pv_value("{0}:{1}:CURR:SP".format(PREFIX, IDN), set_value)
            self.ca.assert_that_pv_is("{0}:{1}:CURR".format(PREFIX, IDN), return_value)
            self.ca.assert_that_pv_is("{0}:{1}:RA".format(PREFIX, IDN), return_value)
