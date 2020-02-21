import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list, get_running_lewis_and_ioc, skip_if_devsim, skip_if_recsim, unstable_test

from common_tests.danfysik import DanfysikCommon, HAS_TRIPPED

from parameterized import parameterized

# Prefix for addressing PVs on this device
PREFIX = "RKNPS_01"

ADR1 = "001"
ID1 = "RQ1"
ADR2 = "002"
ID2 = "RB1"

ADR3 = "003"
ID3 = "RB3"
ADR4 = "004"
ID4 = "RB4"


CLEAR_STATUS = "."*24
IDS = [ID1, ID2, ID3, ID4]

PSU_ADDRESSES = [ADR1, ADR2, ADR3, ADR4]

IOCS = [
    {
        "name": PREFIX,
        "directory": get_default_ioc_dir("RKNPS"),
        "macros": {
            "CHAIN1_ID1": ID1,
            "CHAIN1_ADR1": ADR1,

            "CHAIN1_ID2": ID2,
            "CHAIN1_ADR2": ADR2,

            "CHAIN1_ID3": ID3,
            "CHAIN1_ADR3": ADR3,

            "CHAIN1_ID4": ID4,
            "CHAIN1_ADR4": ADR4,
        },
        "pv_for_existence": "{}:DISABLE".format(ID1),
        "emulator": "rknps",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

INTERLOCKS = ("TRANS",
              "DCOC",
              "DCOL",
              "REGMOD",
              "PREREG",
              "PHAS",
              "MPSWATER",
              "EARTHLEAK",
              "THERMAL",
              "MPSTEMP",
              "DOOR",
              "MAGWATER",
              "MAGTEMP",
              "MPSREADY")


class RknpsTests(DanfysikCommon, unittest.TestCase):
    """
    Tests for the RIKEN Multidrop Danfysik Power Supplies.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("rknps", PREFIX)
        self.ca = ChannelAccess(device_prefix=PREFIX, default_timeout=60)
        self._lewis.backdoor_set_on_device("connected", True)

        self.current_readback_factor = 1000

        self.id_prefixes = [ID + ":" for ID in IDS]

        for id_prefix in self.id_prefixes:
            self.ca.assert_that_pv_exists("{}ADDRESS".format(id_prefix), timeout=30)

    def disconnect_device(self):
        """RIKEN PSU emulator disconnects slightly differently"""
        self._lewis.backdoor_set_on_device("connected", False)

    def set_voltage(self, voltage):
        self._lewis.backdoor_set_on_device("set_all_volt_values", voltage)

    def _activate_interlocks(self):
        """
        Activate both interlocks in the emulator.
        """
        self._lewis.backdoor_set_on_device("set_all_interlocks", True)

    def _deactivate_interlocks(self):
        """
        Deactivate both interlocks in the emulator.
        """
        if IOCRegister.is_using_recsim:
            for IDN in IDS:
                self._ioc.set_simulated_value("{}:SIM:STATUS".format(IDN), CLEAR_STATUS)
        else:
            self._lewis.backdoor_set_on_device("set_all_interlocks", False)

    @skip_if_recsim("Interlock statuses depend on emulator")
    def test_WHEN_interlocks_are_active_THEN_ilk_is_Interlocked(self):
        self._activate_interlocks()
        for IDN in IDS:
            self.ca.assert_that_pv_is("{0}:ILK".format(IDN), HAS_TRIPPED[True])

    @skip_if_recsim("Interlock statuses depend on emulator")
    def test_WHEN_interlocks_are_inactive_THEN_ilk_is_not_Interlocked(self):
        self._deactivate_interlocks()
        for IDN in IDS:
            self.ca.assert_that_pv_is("{0}:ILK".format(IDN), HAS_TRIPPED[False])

    @skip_if_recsim("In rec sim this test fails as the changes are not propagated to all appropriate PVs")
    def test_GIVEN_a_positive_value_and_emulator_in_use_WHEN_current_is_set_THEN_values_are_as_expected(self):
        expected_value = 480
        for IDN in IDS:
            self.ca.set_pv_value("{0}:CURR:SP".format(IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:CURR".format(IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:RA".format(IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:POL".format(IDN), "+")

    @skip_if_recsim("In rec sim this test fails as the changes are not propagated to all appropriate PVs")
    def test_GIVEN_a_negative_value_and_emulator_in_use_WHEN_current_is_set_THEN_values_are_as_expected(self):
        expected_value = -123
        for IDN in IDS:
            self.ca.set_pv_value("{0}:CURR:SP".format(IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:CURR".format(IDN), expected_value)
            self.ca.assert_that_pv_is("{0}:RA".format(IDN), abs(expected_value))
            self.ca.assert_that_pv_is("{0}:POL".format(IDN), "-")

    @skip_if_devsim("In dev sim this test fails as the emulator "
                    "handles the difference in values between write and read")
    def test_GIVEN_a_negative_value_and_emulator_not_in_use_WHEN_current_is_set_THEN_values_are_as_expected(self):
        set_value = -123
        return_value = set_value*1000
        for IDN in IDS:
            self.ca.set_pv_value("{0}:CURR:SP".format(IDN), set_value)
            self.ca.assert_that_pv_is("{0}:CURR".format(IDN), return_value)
            self.ca.assert_that_pv_is("{0}:RA".format(IDN), return_value)

    @skip_if_recsim("Power updates through protocol redirection")
    def test_GIVEN_rb3_status_changes_THEN_rb3_banner_pv_updates_correctly(self):
        if "RB3" not in IDS:
            self.fail("Didn't find RB3 for test.")

        for powered_on in (True, False):
            self.ca.set_pv_value("RB3:POWER:SP", powered_on)
            self.ca.assert_that_pv_is("RB3:BANNER",
                                      "on; beam to ports 1,2" if powered_on else "off; ports 1,2 safe")

    @skip_if_recsim("Power updates through protocol redirection")
    def test_GIVEN_rb4_status_changes_THEN_rb4_banner_pv_updates_correctly(self):
        if "RB4" not in IDS:
            self.fail("Didn't find RB4 for test.")

        for powered_on in (True, False):
            self.ca.set_pv_value("RB4:POWER:SP", powered_on)
            self.ca.assert_that_pv_is("RB4:BANNER",
                                      "on; beam to ports 3,4" if powered_on else "off; ports 3,4 safe")

    @parameterized.expand(INTERLOCKS)
    @skip_if_recsim("Test requires emulator to change interlock state")
    def test_GIVEN_interlock_status_WHEN_read_all_status_THEN_status_is_as_expected(self, interlock):
        for boolean_value, expected_value in HAS_TRIPPED.items():
            for IDN, ADDR in zip(IDS, PSU_ADDRESSES):
                # GIVEN
                self._lewis.backdoor_run_function_on_device("set_{0}".format(interlock), (boolean_value, ADDR))

                # THEN
                self.ca.assert_that_pv_is("{0}:ILK:{1}".format(IDN, interlock), expected_value)
                self.ca.assert_that_pv_alarm_is("{0}:ILK:{1}".format(IDN, interlock), self.ca.Alarms.NONE)

    @parameterized.expand(INTERLOCKS)
    @skip_if_recsim("Test requires emulator")
    def test_GIVEN_individual_interlock_read_WHEN_device_not_connected_THEN_interlock_PV_in_alarm(self, interlock):
        # WHEN
        self._lewis.backdoor_set_on_device("connected", False)

        # THEN
        for IDN, ADDR in zip(IDS, PSU_ADDRESSES):
            self.ca.assert_that_pv_alarm_is("{0}:ILK:{1}".format(IDN, interlock), self.ca.Alarms.INVALID)

    @parameterized.expand(parameterized_list([
        ("FAULT STATE", 0, 0),
        ("BEND 1", 1, 0),
        ("BEND 2", 0, 1),
        ("SEPTUM", 1, 1),
    ]))
    @skip_if_devsim("DAQ does not exist in devsim")
    def test_GIVEN_mock_DAQ_inputs_THEN_RB2_mode_is_correct(self, _, state, val1, val2):
        self.ca.set_pv_value("DAQ:R04:DATA:SIM", val1)
        self.ca.set_pv_value("DAQ:R05:DATA:SIM", val2)
        self.ca.assert_that_pv_is("RB2:MODE", state)

    @parameterized.expand(parameterized_list([
        ("FAULT (LOW)", 0, 0),
        ("PORT 3 (RQ18-20)", 1, 0),
        ("PORT 4 (RQ21-23)", 0, 1),
        ("FAULT (HIGH)", 1, 1),
    ]))
    @skip_if_devsim("DAQ does not exist in devsim")
    def test_GIVEN_mock_DAQ_inputs_THEN_PORT3_4_mode_is_correct(self, _, state, val1, val2):
        self.ca.set_pv_value("DAQ:R02:DATA:SIM", val1)
        self.ca.set_pv_value("DAQ:R03:DATA:SIM", val2)
        self.ca.assert_that_pv_is("PORT3_4:MODE", state)

    @skip_if_devsim("DAQ does not exist in devsim")
    def test_GIVEN_fault_condition_THEN_RB2_alarms_correct(self):
        self.ca.set_pv_value("DAQ:R04:DATA:SIM", 0)
        self.ca.set_pv_value("DAQ:R05:DATA:SIM", 0)
        self.ca.assert_that_pv_alarm_is("RB2:MODE", ChannelAccess.Alarms.MAJOR)

    @skip_if_devsim("DAQ does not exist in devsim")
    def test_GIVEN_high_fault_condition_THEN_PORT3_4_alarms_correct(self):
        self.ca.set_pv_value("DAQ:R02:DATA:SIM", 1)
        self.ca.set_pv_value("DAQ:R03:DATA:SIM", 1)
        self.ca.assert_that_pv_alarm_is("PORT3_4:MODE", ChannelAccess.Alarms.MAJOR)

    @skip_if_devsim("DAQ does not exist in devsim")
    def test_GIVEN_low_fault_condition_THEN_PORT3_4_alarms_correct(self):
        self.ca.set_pv_value("DAQ:R02:DATA:SIM", 0)
        self.ca.set_pv_value("DAQ:R03:DATA:SIM", 0)
        self.ca.assert_that_pv_alarm_is("PORT3_4:MODE", ChannelAccess.Alarms.MAJOR)

