import unittest

from common_tests.kepco import (
    KepcoTests,
    DEVICE_PREFIX,
    emulator_name,
    IDN_NO_REM,
    IDN_REM,
    MAX_CURRENT,
)

from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import skip_if_recsim, parameterized_list

from parameterized import parameterized

from distutils.util import strtobool
import time


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEPCO"),
        "macros": {"CURRENT_MAX": MAX_CURRENT, "REMOTE_ON_SET": "NO"},
        "emulator": emulator_name,
        "ioc_launcher_class": ProcServLauncher,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class KepcoNoRemTests(KepcoTests, unittest.TestCase):
    """
    Tests for the KEPCO that has no SYS:REM command available.
    """

    def setUp(self):
        super(KepcoNoRemTests, self).setUp()
        self._set_IDN(IDN_NO_REM[0], IDN_NO_REM[1])

    def lewis_set_and_assert_list(self, lewis_vars_and_vals):
        for var, val in lewis_vars_and_vals:
            self._lewis.backdoor_set_and_assert_set(var, val)

    def assert_lewis_set_counts_incremented(self, lewis_vars_and_vals):
        self.assert_lewis_set_counts_set_correctly(lewis_vars_and_vals, lambda x: x + 1)

    def assert_lewis_set_counts_not_incremented(self, lewis_vars_and_vals):
        self.assert_lewis_set_counts_set_correctly(lewis_vars_and_vals, lambda x: x)

    def assert_lewis_set_counts_set_correctly(self, lewis_vars_and_vals, set_func):
        # Assert that correct calls have been made to write to setpoints
        error_message_calls = ""
        for var, val in lewis_vars_and_vals:
            try:
                self._lewis.assert_that_emulator_value_is(var, set_func(val), cast=int)
            except AssertionError as e:
                error_message_calls += "\n{}\n{}".format(var, e.message)
        if error_message_calls != "":
            raise AssertionError("Failed to call sets:{}".format(error_message_calls))

    @parameterized.expand(
        parameterized_list(
            [
                (IDN_NO_REM[0], IDN_NO_REM[1], {"RESET_ON_START": 1}),
                (IDN_NO_REM[0], IDN_NO_REM[1], {"RESET_ON_START": 2}),
                (IDN_REM[0], IDN_REM[1], {"RESET_ON_START": 2}),
            ]
        )
    )
    @skip_if_recsim("Lewis not available in recsim")
    def test_GIVEN_kepco_started_THEN_reset_and_params_resent(
        self, _, idn_no_firmware, firmware, macros
    ):
        # Reset data
        self._lewis.backdoor_run_function_on_device("reset")
        self._set_IDN(idn_no_firmware, firmware)

        # Set setpoint pvs to something different to their initial values
        # Keep dict to check autosave has maintained the sets after reset
        pv_values = {
            "CURRENT:SP": float(self._lewis.backdoor_get_from_device("setpoint_current")) + 5.0,
            "VOLTAGE:SP": float(self._lewis.backdoor_get_from_device("setpoint_voltage")) + 5.0,
            "OUTPUTMODE:SP": "VOLTAGE"
            if self.ca.get_pv_value("OUTPUTMODE:SP") == "CURRENT"
            else "CURRENT",
            "OUTPUTSTATUS:SP": "OFF" if self.ca.get_pv_value("OUTPUTSTATUS:SP") == "ON" else "ON",
        }
        for pv, value in pv_values.items():
            self.ca.set_pv_value(pv, value)
            self.ca.assert_that_pv_is(pv, value)

        # Make sure autosave writes the value
        self._ioc.force_manual_save()

        # Set counts to zero and remote mode to false
        # We want lewis_vars and lewis_vals separate as they are checked later
        lewis_vars = [
            "voltage_set_count",
            "current_set_count",
            "output_mode_set_count",
            "output_status_set_count",
        ]
        lewis_vals = [0, 0, 0, 0]
        self.lewis_set_and_assert_list(
            zip(lewis_vars + ["reset_count", "remote_comms_enabled"], lewis_vals + [0, False])
        )

        # Restart the ioc, initiating a reset and sending of values after 100 microseconds
        with self._ioc.start_with_macros(macros, "VOLTAGE"):
            # Assert reset occurred
            self._lewis.assert_that_emulator_value_is("reset_count", 1, cast=int)
            self._lewis.assert_that_emulator_value_is("remote_comms_enabled", True, cast=strtobool)
            # Wait for reset to be done as is done in the IOC
            time.sleep(1)

            # Assert correct calls made
            self.assert_lewis_set_counts_incremented(zip(lewis_vars, lewis_vals))

            # Assert autosave has correctly set pvs
            self.ca.assert_dict_of_pvs_have_given_values(pv_values)
