import unittest
from contextlib import contextmanager

import time
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "IPS_01"
EMULATOR_NAME = "ips"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("IPS"),
        "emulator": EMULATOR_NAME,
    },
]


# Only run tests in DEVSIM. Unable to produce detailed enough functionality to be useful in recsim.
TEST_MODES = [TestModes.DEVSIM]

TEST_VALUES = -0.12345, 7.654321  # Should be able to handle negative polarities

TOLERANCE = 0.0001

HEATER_OFF_STATES = ["Off Mag at 0", "Off Mag at F"]

# Time to wait for the heater to warm up/cool down
# On a real system this is 30s but speed it up a bit for the sake of tests.
HEATER_WAIT_TIME = 10


class IpsTests(unittest.TestCase):
    """
    Tests for the Ips IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)

        # Wait for some critical pvs to be connected.
        for pv in ["PERSISTENTMAGNETFIELD", "FIELD", "FIELD:SP:RBV", "HEATER:STATUS"]:
            self.ca.wait_for(pv)

        # Ensure in the correct mode
        self.ca.set_pv_value("CONTROL:SP", "Remote & Unlocked")
        self.ca.set_pv_value("ACTIVITY:SP", "To Setpoint")

        # Don't run reset as the sudden change of state confuses the IOC's state machine. No matter what the initial
        # state of the device the SNL should be able to deal with it.
        # self._lewis.backdoor_run_function_on_device("reset")

        self.ca.set_pv_value("HEATER:WAITTIME", HEATER_WAIT_TIME)

        self.ca.set_pv_value("FIELDSWEEPRATE:SP", 10)

    def tearDown(self):
        self.assertEqual(self._lewis.backdoor_get_from_device("quenched"), "False")

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def _assert_field_is(self, field, timeout=None, check_stable=False):
        self.ca.assert_that_pv_is_number("FIELD", field, tolerance=TOLERANCE, timeout=timeout)
        if check_stable:
            self.ca.assert_pv_value_is_unchanged("FIELD", wait=30)
            self.ca.assert_that_pv_is_number("FIELD", field, tolerance=TOLERANCE)

    def _assert_heater_is(self, heater_state, timeout=None):
        self.ca.assert_that_pv_is("HEATER:STATUS:SP", "On" if heater_state else "Off", timeout=timeout)
        if heater_state:
            self.ca.assert_that_pv_is("HEATER:STATUS", "On", timeout=timeout)
        else:
            self.ca.assert_that_pv_is_one_of("HEATER:STATUS", HEATER_OFF_STATES, timeout=timeout)

    def _set_and_check_persistent_mode(self, mode):
        self.ca.assert_setting_setpoint_sets_readback("YES" if mode else "NO", "PERSISTENT")

    def test_GIVEN_persistent_mode_enabled_WHEN_magnet_told_to_go_to_field_setpoint_THEN_goes_to_that_setpoint_and_psu_ramps_to_zero(self):
        """
        Happy path test; magnet acts as we want it to.
        """
        self._set_and_check_persistent_mode(True)

        for val in TEST_VALUES:
            # Field in the magnet already from persistent mode.
            persistent_field = float(self.ca.get_pv_value("PERSISTENTMAGNETFIELD"))

            # Set the new field. This will cause all of the following events based on the state machine.
            self.ca.set_pv_value("FIELD:SP", val)

            # PSU should be ramped to match the persistent field inside the magnet
            self._assert_field_is(persistent_field)
            self.ca.assert_that_pv_is("ACTIVITY", "To Setpoint")

            # Then it is safe to turn on the heater
            self._assert_heater_is(True, timeout=HEATER_WAIT_TIME*2)

            # Assert that value gets passed to device by SNL. SNL waits 30s for the heater to cool down/warm up
            # after being set.
            self._assert_field_is(val, timeout=HEATER_WAIT_TIME*2)

            # Now that the correct current is in the magnet, the SNL should turn the heater off
            self._assert_heater_is(False, timeout=HEATER_WAIT_TIME*2)

            # Now that the heater is off, can ramp down the PSU to zero (SNL waits some time for heater to be off before
            # ramping PSU to zero)
            self._assert_field_is(0, timeout=HEATER_WAIT_TIME*2)
            self.ca.assert_that_pv_is("ACTIVITY", "To Zero")

            # ...And the magnet should now be in the right state!
            self.ca.assert_that_pv_is_number("PERSISTENTMAGNETFIELD", val, tolerance=TOLERANCE)

    def test_GIVEN_non_persistent_mode_WHEN_magnet_told_to_go_to_field_setpoint_THEN_goes_to_that_setpoint_and_psu_does_not_ramp_to_zero(self):
        """
        Happy path test; magnet acts as we want it to.
        """
        self._set_and_check_persistent_mode(False)

        for val in TEST_VALUES:
            # Field in the magnet already from persistent mode.
            persistent_field = float(self.ca.get_pv_value("PERSISTENTMAGNETFIELD"))

            # Set the new field. This will cause all of the following events based on the state machine.
            self.ca.set_pv_value("FIELD:SP", val)

            # PSU should be ramped to match the persistent field inside the magnet (if there was one)
            self._assert_field_is(persistent_field, timeout=HEATER_WAIT_TIME*2)

            # Then it is safe to turn on the heater (the heater is explicitly switched on and we wait for it even if it
            # was already on out of an abundance of caution).
            self._assert_heater_is(True, timeout=HEATER_WAIT_TIME*2)

            # Assert that value gets passed to device by SNL. SNL waits 30s for the heater to cool down/warm up
            # after being set.
            self._assert_field_is(val, timeout=HEATER_WAIT_TIME*2)

            # ...And the magnet should now be in the right state!
            self.ca.assert_that_pv_is_number("PERSISTENTMAGNETFIELD", val, tolerance=TOLERANCE)

            # And the PSU should remain stable providing the required current/field
            self._assert_field_is(val, check_stable=True)

    @contextmanager
    def _backdoor_magnet_quench(self, reason="Test framework quench"):
        self._lewis.backdoor_run_function_on_device("quench", [reason])
        try:
            yield
        finally:
            # Get back out of the quenched state. This is because the tearDown method checks that magnet has not
            # quenched.
            self._lewis.backdoor_run_function_on_device("unquench")
            # Wait for IOC to notice quench state has gone away
            self.ca.assert_pv_alarm_is("STS:SYSTEM:FAULT", self.ca.ALARM_NONE)

    def test_GIVEN_magnet_quenches_while_at_field_THEN_ioc_displays_this_quench_in_statuses(self):

        for field in TEST_VALUES:
            self._set_and_check_persistent_mode(False)
            self.ca.set_pv_value("FIELD:SP", field)
            self._assert_field_is(field, timeout=HEATER_WAIT_TIME*2)

            with self._backdoor_magnet_quench():
                self.ca.assert_that_pv_is("STS:SYSTEM:FAULT", "Quenched")
                self.ca.assert_pv_alarm_is("STS:SYSTEM:FAULT", self.ca.ALARM_MAJOR)
                self.ca.assert_that_pv_is("CONTROL", "Auto-Run-Down")
                self.ca.assert_pv_alarm_is("CONTROL", self.ca.ALARM_MAJOR)

                # The trip field should be the field at the point when the magnet quenched.
                self.ca.assert_that_pv_is_number("TRIPFIELD", field, tolerance=TOLERANCE)

                # Field should be set to zero by emulator (mirroring what the field ought to do in the real device)
                self.ca.assert_that_pv_is_number("FIELD", 0, tolerance=TOLERANCE)
                self.ca.assert_that_pv_is_number("PERSISTENTMAGNETFIELD", 0, tolerance=TOLERANCE)

    def test_WHEN_inductance_set_via_backdoor_THEN_value_in_ioc_updates(self):
        for val in TEST_VALUES:
            self._lewis.backdoor_set_on_device("inductance", val)
            self.ca.assert_that_pv_is_number("MAGNETINDUCTANCE", val, tolerance=TOLERANCE)

    def test_WHEN_measured_current_set_via_backdoor_THEN_value_in_ioc_updates(self):
        for val in TEST_VALUES:
            self._lewis.backdoor_set_on_device("measured_current", val)
            self.ca.assert_that_pv_is_number("MEASUREDMAGNETCURRENT", val, tolerance=TOLERANCE)

    def test_WHEN_sweep_rate_set_THEN_sweep_rate_on_ioc_updates(self):
        for val in TEST_VALUES:
            self.ca.set_pv_value("FIELDSWEEPRATE:SP", val)
            self.ca.assert_that_pv_is_number("FIELDSWEEPRATE:SP", val, tolerance=TOLERANCE)
