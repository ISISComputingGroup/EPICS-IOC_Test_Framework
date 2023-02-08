import unittest
from contextlib import contextmanager

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, unstable_test
from parameterized import parameterized


DEVICE_PREFIX = "IPS_01"
EMULATOR_NAME = "ips"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("IPS"),
        "emulator": EMULATOR_NAME,
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "MANAGER_ASG": "DEFAULT",
            "MAX_SWEEP_RATE": "1.0",
            "HEATER_WAITTIME": "10",  # On a real system the macro has a default of 60s,
                                      # but speed it up a bit for the sake of tests.
        }
    },
]


# Only run tests in DEVSIM. Unable to produce detailed enough functionality to be useful in recsim.
TEST_MODES = [TestModes.DEVSIM]

TEST_VALUES = -0.12345, 6.54321  # Should be able to handle negative polarities
TEST_SWEEP_RATES = 0.001, 0.9876  # Rate can't be negative or >1

TOLERANCE = 0.0001

HEATER_OFF_STATES = ["Off Mag at 0", "Off Mag at F"]

# Time to wait for the heater to warm up/cool down (extracted from IOC macros above)
HEATER_WAIT_TIME = float((IOCS[0].get('macros').get('HEATER_WAITTIME')))

ACTIVITY_STATES = ["Hold", "To Setpoint", "To Zero", "Clamped"]

# Generate all the control commands to test that remote and unlocked is set for
# Chain flattens the list
CONTROL_COMMANDS_WITH_VALUES = [("FIELD", 0.1), ("FIELD:RATE", 0.1), ("SWEEPMODE:PARAMS", "Tesla Fast")]
for activity_state in ACTIVITY_STATES:
    CONTROL_COMMANDS_WITH_VALUES.append(("ACTIVITY", activity_state))
for heater_off_state in HEATER_OFF_STATES:
    CONTROL_COMMANDS_WITH_VALUES.append(("HEATER:STATUS", heater_off_state))

CONTROL_COMMANDS_WITHOUT_VALUES = ["SET:COMMSRES"]


class IpsTests(unittest.TestCase):
    """
    Tests for the Ips IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        # Some changes happen on the order of HEATER_WAIT_TIME seconds. Use a significantly longer timeout
        # to capture a few heater wait times plus some time for PVs to update.
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=HEATER_WAIT_TIME*10)

        # Wait for some critical pvs to be connected.
        for pv in ["MAGNET:FIELD:PERSISTENT", "FIELD", "FIELD:SP:RBV", "HEATER:STATUS"]:
            self.ca.assert_that_pv_exists(pv)

        # Ensure in the correct mode
        self.ca.set_pv_value("CONTROL:SP", "Remote & Unlocked")
        self.ca.set_pv_value("ACTIVITY:SP", "To Setpoint")

        # Don't run reset as the sudden change of state confuses the IOC's state machine. No matter what the initial
        # state of the device the SNL should be able to deal with it.
        # self._lewis.backdoor_run_function_on_device("reset")

        self.ca.set_pv_value("FIELD:RATE:SP", 10)
        # self.ca.assert_that_pv_is_number("FIELD:RATE:SP", 10)

        self.ca.process_pv("FIELD:SP")

        # Wait for statemachine to reach "at field" state before every test.
        self.ca.assert_that_pv_is("STATEMACHINE", "At field")

    def tearDown(self):
        # Wait for statemachine to reach "at field" state after every test.
        self.ca.assert_that_pv_is("STATEMACHINE", "At field")

        self.assertEqual(self._lewis.backdoor_get_from_device("quenched"), "False")

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def _assert_field_is(self, field, check_stable=False):
        self.ca.assert_that_pv_is_number("FIELD", field, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("FIELD:USER", field, tolerance=TOLERANCE)
        if check_stable:
            self.ca.assert_that_pv_value_is_unchanged("FIELD", wait=30)
            self.ca.assert_that_pv_is_number("FIELD", field, tolerance=TOLERANCE, timeout=10)
            self.ca.assert_that_pv_is_number("FIELD:USER", field, tolerance=TOLERANCE, timeout=10)

    def _assert_heater_is(self, heater_state):
        self.ca.assert_that_pv_is("HEATER:STATUS:SP", "On" if heater_state else "Off")
        if heater_state:
            self.ca.assert_that_pv_is("HEATER:STATUS", "On",)
        else:
            self.ca.assert_that_pv_is_one_of("HEATER:STATUS", HEATER_OFF_STATES)

    def _set_and_check_persistent_mode(self, mode):
        self.ca.assert_setting_setpoint_sets_readback("YES" if mode else "NO", "PERSISTENT")

    @parameterized.expand(val for val in parameterized_list(TEST_VALUES))
    def test_GIVEN_persistent_mode_enabled_WHEN_magnet_told_to_go_to_field_setpoint_THEN_goes_to_that_setpoint_and_psu_ramps_to_zero(self, _, val):

        self._set_and_check_persistent_mode(True)

        # Field in the magnet already from persistent mode.
        persistent_field = float(self.ca.get_pv_value("MAGNET:FIELD:PERSISTENT"))

        # Set the new field. This will cause all of the following events based on the state machine.
        self.ca.set_pv_value("FIELD:SP", val)

        # PSU should be ramped to match the persistent field inside the magnet
        self._assert_field_is(persistent_field)
        self.ca.assert_that_pv_is("ACTIVITY", "To Setpoint")

        # Then it is safe to turn on the heater
        self._assert_heater_is(True)

        # Assert that value gets passed to device by SNL. SNL waits 30s for the heater to cool down/warm up
        # after being set.
        self._assert_field_is(val)

        # Now that the correct current is in the magnet, the SNL should turn the heater off
        self._assert_heater_is(False)

        # Now that the heater is off, can ramp down the PSU to zero (SNL waits some time for heater to be off before
        # ramping PSU to zero)
        self.ca.assert_that_pv_is_number("FIELD", 0, tolerance=TOLERANCE)  # PSU field
        self.ca.assert_that_pv_is_number("MAGNET:FIELD:PERSISTENT", val, tolerance=TOLERANCE)  # Persistent field
        self.ca.assert_that_pv_is_number("FIELD:USER", val, tolerance=TOLERANCE)  # User field should be tracking persistent field here
        self.ca.assert_that_pv_is("ACTIVITY", "To Zero")

        # ...And the magnet should now be in the right state!
        self.ca.assert_that_pv_is("STATEMACHINE", "At field")
        self.ca.assert_that_pv_is_number("MAGNET:FIELD:PERSISTENT", val, tolerance=TOLERANCE)

        # "User" field should take the value put in the setpoint, even when the actual field provided by the supply
        # drops to zero
        self.ca.assert_that_pv_is_number("FIELD", 0, tolerance=TOLERANCE)  # PSU field
        self.ca.assert_that_pv_is_number("MAGNET:FIELD:PERSISTENT", val, tolerance=TOLERANCE)  # Persistent field
        self.ca.assert_that_pv_is_number("FIELD:USER", val, tolerance=TOLERANCE)  # User field should be tracking persistent field here

    @parameterized.expand(val for val in parameterized_list(TEST_VALUES))
    def test_GIVEN_non_persistent_mode_WHEN_magnet_told_to_go_to_field_setpoint_THEN_goes_to_that_setpoint_and_psu_does_not_ramp_to_zero(self, _, val):

        self._set_and_check_persistent_mode(False)

        # Field in the magnet already from persistent mode.
        persistent_field = float(self.ca.get_pv_value("MAGNET:FIELD:PERSISTENT"))

        # Set the new field. This will cause all of the following events based on the state machine.
        self.ca.set_pv_value("FIELD:SP", val)

        # PSU should be ramped to match the persistent field inside the magnet (if there was one)
        self._assert_field_is(persistent_field)

        # Then it is safe to turn on the heater (the heater is explicitly switched on and we wait for it even if it
        # was already on out of an abundance of caution).
        self._assert_heater_is(True)

        # Assert that value gets passed to device by SNL. SNL waits 30s for the heater to cool down/warm up
        # after being set.
        self._assert_field_is(val)

        # ...And the magnet should now be in the right state!
        self.ca.assert_that_pv_is_number("MAGNET:FIELD:PERSISTENT", val, tolerance=TOLERANCE)

        # And the PSU should remain stable providing the required current/field
        self.ca.assert_that_pv_is("STATEMACHINE", "At field")
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
            self.ca.assert_that_pv_alarm_is("STS:SYSTEM:FAULT", self.ca.Alarms.NONE)

    @parameterized.expand(field for field in parameterized_list(TEST_VALUES))
    def test_GIVEN_magnet_quenches_while_at_field_THEN_ioc_displays_this_quench_in_statuses(self, _, field):

        self._set_and_check_persistent_mode(False)
        self.ca.set_pv_value("FIELD:SP", field)
        self._assert_field_is(field)
        self.ca.assert_that_pv_is("STATEMACHINE", "At field")

        with self._backdoor_magnet_quench():
            self.ca.assert_that_pv_is("STS:SYSTEM:FAULT", "Quenched")
            self.ca.assert_that_pv_alarm_is("STS:SYSTEM:FAULT", self.ca.Alarms.MAJOR)
            self.ca.assert_that_pv_is("CONTROL", "Auto-Run-Down")
            self.ca.assert_that_pv_alarm_is("CONTROL", self.ca.Alarms.MAJOR)

            # The trip field should be the field at the point when the magnet quenched.
            self.ca.assert_that_pv_is_number("FIELD:TRIP", field, tolerance=TOLERANCE)

            # Field should be set to zero by emulator (mirroring what the field ought to do in the real device)
            self.ca.assert_that_pv_is_number("FIELD", 0, tolerance=TOLERANCE)
            self.ca.assert_that_pv_is_number("FIELD:USER", 0, tolerance=TOLERANCE)
            self.ca.assert_that_pv_is_number("MAGNET:FIELD:PERSISTENT", 0, tolerance=TOLERANCE)

    @parameterized.expand(val for val in parameterized_list(TEST_VALUES))
    def test_WHEN_inductance_set_via_backdoor_THEN_value_in_ioc_updates(self, _, val):
        self._lewis.backdoor_set_on_device("inductance", val)
        self.ca.assert_that_pv_is_number("MAGNET:INDUCTANCE", val, tolerance=TOLERANCE)

    @parameterized.expand(val for val in parameterized_list(TEST_VALUES))
    def test_WHEN_measured_current_set_via_backdoor_THEN_value_in_ioc_updates(self, _, val):
        self._lewis.backdoor_set_on_device("measured_current", val)
        self.ca.assert_that_pv_is_number("MAGNET:CURR:MEAS", val, tolerance=TOLERANCE)

    @parameterized.expand(val for val in parameterized_list(TEST_SWEEP_RATES))
    def test_WHEN_sweep_rate_set_THEN_sweep_rate_on_ioc_updates(self, _, val):
        self.ca.set_pv_value("FIELD:RATE:SP", val)
        self.ca.assert_that_pv_is_number("FIELD:RATE:SP", val, tolerance=TOLERANCE)
        self.ca.assert_that_pv_is_number("FIELD:RATE", val, tolerance=TOLERANCE)
        self.ca.assert_that_pv_alarm_is("FIELD:RATE", self.ca.Alarms.NONE)

    @parameterized.expand(activity_state for activity_state in parameterized_list(ACTIVITY_STATES))
    @unstable_test()
    def test_WHEN_activity_set_via_backdoor_to_clamped_THEN_alarm_major_ELSE_no_alarm(self, _, activity_state):
        self.ca.set_pv_value("ACTIVITY", activity_state)
        if activity_state == "Clamped":
            self.ca.assert_that_pv_alarm_is("ACTIVITY", "MAJOR")
        else:
            self.ca.assert_that_pv_alarm_is("ACTIVITY", "NO_ALARM")

    @parameterized.expand(control_command for control_command in parameterized_list(CONTROL_COMMANDS_WITH_VALUES))
    def test_WHEN_control_command_value_set_THEN_remote_unlocked_set(self, _, control_pv, set_value):
        self.ca.set_pv_value("CONTROL", "Local & Locked")
        self.ca.set_pv_value(control_pv, set_value)
        self.ca.assert_that_pv_is("CONTROL", "Remote & Unlocked")

    @parameterized.expand(control_pv for control_pv in parameterized_list(CONTROL_COMMANDS_WITHOUT_VALUES))
    def test_WHEN_control_command_processed_THEN_remote_unlocked_set(self, _, control_pv):
        self.ca.set_pv_value("CONTROL", "Local & Locked")
        self.ca.process_pv(control_pv)
        self.ca.assert_that_pv_is("CONTROL", "Remote & Unlocked")

    # original problem/complaint:
    # in non-persistent mode, heater wait time always implemented, therefore too slow to set new fields
    def test_GIVEN_at_field_in_non_persistent_mode_WHEN_new_field_set_THEN_no_wait_for_heater(self):
        # arrange: set mode to non-persistent, set field
        self._set_and_check_persistent_mode(False)
        self.ca.set_pv_value("FIELD:SP", 3.21)
        self._assert_field_is(3.21)
        self.ca.assert_that_pv_is("STATEMACHINE", "At field")

        # act: set new field
        self.ca.set_pv_value("FIELD:SP", 4.56)

        # assert: field starts to change by tolerance within timeout, then reaches within second timeout
        # timeout present to prove new setpoint moved to _without_ waiting for heater, if already on
        self.ca.assert_that_pv_is_not_number("FIELD", 3.21, tolerance=0.01, timeout=20)
        self.ca.assert_that_pv_is_number("FIELD", 4.56, tolerance=0.01, timeout=60)
