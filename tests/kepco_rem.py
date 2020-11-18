import unittest

from common_tests.kepco import KepcoTests, DEVICE_PREFIX, emulator_name, IDN_NO_REM, IDN_REM

from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import skip_if_recsim, parameterized_list

from distutils.util import strtobool

from parameterized import parameterized

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEPCO"),
        "macros": {},
        "emulator": emulator_name,
        "ioc_launcher_class": ProcServLauncher,
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class KepcoRemTests(KepcoTests, unittest.TestCase):
    """
    Tests for the KEPCO that has a SYST:REM command available.
    """

    def setUp(self):
        super(KepcoRemTests, self).setUp()
        self._set_IDN(IDN_REM[0], IDN_REM[1])

    @parameterized.expand(parameterized_list([
        "OUTPUTMODE:SP",
        "CURRENT:SP",
        "VOLTAGE:SP",
        "OUTPUTSTATUS:SP",
    ]))
    @skip_if_recsim("Complex behaviour not simulated in recsim")
    def test_GIVEN_psu_in_local_mode_WHEN_setpoint_is_sent_THEN_power_supply_put_into_remote_first(self, _,
                                                                                                   setpoint_pv):
        self._lewis.backdoor_set_on_device("remote_comms_enabled", False)
        self._lewis.assert_that_emulator_value_is("remote_comms_enabled", False, cast=strtobool)

        self.ca.process_pv(setpoint_pv)

        self._lewis.assert_that_emulator_value_is("remote_comms_enabled", True, cast=strtobool)

    @parameterized.expand(parameterized_list([
        (IDN_REM[0], IDN_REM[1], {}),
        (IDN_REM[0], IDN_REM[1], {"RESET_ON_START": 0}),
        (IDN_REM[0], IDN_REM[1], {"RESET_ON_START": 1}),
    ]))
    @skip_if_recsim("Lewis not available in recsim")
    def test_GIVEN_kepco_firmware_supports_SYSTREM_THEN_remote_command_sent_AND_no_reset(
            self, _, idn_no_firmware, firmware, macros):
        self._set_IDN(idn_no_firmware, firmware)
        self._lewis.backdoor_set_and_assert_set("reset_count", 0)
        self._lewis.backdoor_set_and_assert_set("remote_comms_enabled", False)

        with self._ioc.start_with_macros(macros, "VOLTAGE"):
            self._lewis.assert_that_emulator_value_is("remote_comms_enabled", True, cast=strtobool)
            self._lewis.assert_that_emulator_value_is("reset_count", 0, cast=int)

    @parameterized.expand(parameterized_list([
        (IDN_NO_REM[0], IDN_NO_REM[1], {}),
        (IDN_NO_REM[0], IDN_NO_REM[1], {"RESET_ON_START": 0})
    ]))
    @skip_if_recsim("Lewis not available in recsim")
    def test_GIVEN_kepco_firmware_does_not_support_SYSTREM_WHEN_on_start_is_0_THEN_no_remote_mode_AND_no_reset(
            self, _, idn_no_firmware, firmware, macros):
        self._set_IDN(idn_no_firmware, firmware)
        self._lewis.backdoor_set_and_assert_set("reset_count", 0)
        self._lewis.backdoor_set_and_assert_set("remote_comms_enabled", False)

        with self._ioc.start_with_macros(macros, "VOLTAGE"):
            self._lewis.assert_that_emulator_value_is("remote_comms_enabled", False, cast=strtobool)
            self._lewis.assert_that_emulator_value_is("reset_count", 0, cast=int)

