import unittest

from common_tests.kepco import KepcoTests, DEVICE_PREFIX, emulator_name

from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import skip_if_recsim

from distutils.util import strtobool
import time


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KEPCO"),
        "macros": {
            "ON_START": 1
        },
        "emulator": emulator_name,
        "ioc_launcher_class": ProcServLauncher,
        "lewis_protocol": "no_rem",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class KepcoNoRemTests(KepcoTests, unittest.TestCase):
    """
    Tests for the KEPCO that has no SYS:REM command available.
    """

    def setUp(self):
        super(KepcoNoRemTests, self).setUp()

    @skip_if_recsim("Lewis not available in recsim")
    def test_GIVEN_kepco_started_THEN_reset_and_params_resent(self):
        # Reset data
        self._lewis.backdoor_run_function_on_device("reset")

        # Set setpoint pvs to something different to their initial values
        pv_values = {
            "CURRENT:SP": float(self._lewis.backdoor_get_from_device("setpoint_current")) + 5.0,
            "VOLTAGE:SP": float(self._lewis.backdoor_get_from_device("setpoint_voltage")) + 5.0,
            "OUTPUTMODE:SP": "VOLTAGE" if self.ca.get_pv_value("OUTPUTMODE:SP") == "CURRENT" else "CURRENT",
            "OUTPUTSTATUS:SP": "OFF" if self.ca.get_pv_value("OUTPUTSTATUS:SP") == "ON" else "ON"
        }
        for pv, value in pv_values.items():
            self.ca.set_pv_value(pv, value)

        # Set counts to zero and remote mode to false
        lewis_vars = ["voltage_set_count", "current_set_count", "output_mode_set_count", "output_status_set_count"]
        lewis_vals = [0, 0, 0, 0]
        for var, val in zip(lewis_vars + ["reset_count", "remote_comms_enabled"], lewis_vals + [0, False]):
            self._lewis.backdoor_set_and_assert_set(var, val)

        # Restart the ioc, initiating a reset and sending of values after 100 microseconds
        self._ioc.start_ioc()

        # Assert reset occurred
        self._lewis.assert_that_emulator_value_is("reset_count", 1, cast=int)
        self._lewis.assert_that_emulator_value_is("remote_comms_enabled", True, cast=strtobool)
        # Wait for reset to be done as is done in the IOC
        time.sleep(1)

        # Assert that correct calls have been made to write to setpoints
        error_message_calls = ""
        for var, val in zip(lewis_vars, lewis_vals):
            try:
                self._lewis.assert_that_emulator_value_is(var, val + 1, cast=int)
            except AssertionError as e:
                error_message_calls += "\n{}".format(e.message)
        if error_message_calls != "":
            raise AssertionError("Failed to call sets:{}".format(error_message_calls))

        # Assert that setpoint pv values have been reapplied
        error_message_setpoints = []
        for pv, value in pv_values.items():
            try:
                self.ca.assert_that_pv_is(pv, value)
            except AssertionError as e:
                error_message_setpoints += "\n{}".format(e.message)
        if error_message_setpoints != "":
            raise AssertionError("Failed to set setpoints:{}".format(error_message_setpoints))

