import os
import unittest
import itertools
from contextlib import contextmanager

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP

# Defines which IOCs talk to which power supplies.
# Key is IOC number (e.g. 1 for RKNPS_01)
# Values are a list of power supplies on this IOC.
# Only IOCs that should be switched off/interlocked should be listed here.
RIKEN_SETUP = {
    1: ["RQ18", "RQ19"],
    2: ["RQ20"],
}


IOCS = [
    {
        "name": "COORD_01",
        "directory": get_default_ioc_dir("COORD"),
        "macros": {},
    },
    {
        "name": "SIMPLE",
        "directory": os.path.join(EPICS_TOP, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple"),
        "macros": {},
    },
]

# Add RKNPS IOCs corresponding to RIKEN_SETUP
for ioc_num, psus in RIKEN_SETUP.iteritems():
    IOCS.append({
        "name": "RKNPS_{:02d}".format(ioc_num),
        "directory": get_default_ioc_dir("RKNPS", iocnum=ioc_num),
        "macros": dict(itertools.chain(
            # This is just a succint way of setting macros like:
            # ADR1 = 001, ADR2 = 002, ...
            # ID1 = RB1, ID2 = RB2, ... (as defined in RIKEN_SETUP above)
            {"ID{}".format(number): name for number, name in enumerate(psus, 1)}.iteritems(),
            {"ADR{}".format(number): "{:03d}".format(number) for number in range(1, len(psus) + 1)}.iteritems()
        )),
    })


# Build a list containing all the power supplies we need in a convenient form that we can easily iterate over.
POWER_SUPPLIES = []
for ioc_num, supplies in RIKEN_SETUP.iteritems():
    for supply in supplies:
        POWER_SUPPLIES.append("RKNPS_{:02d}:{}".format(ioc_num, supply))


INPUT_PV = "SIMPLE:VALUE1"
ACKNOWLEDGEMENT_PV = "SIMPLE:VALUE2"


class RikenPortChangeoverTests(unittest.TestCase):
    """
    Tests for a riken port changeover.
    """

    def _set_input_pv(self, ok_to_run_psus):
        self.ca.set_pv_value("{}:SP".format(INPUT_PV), 1 if ok_to_run_psus else 0)

    def _set_power_supply_state(self, supply, on):
        self.ca.set_pv_value("{}:POWER:SP".format(supply), 1 if on else 0)
        self.ca.assert_that_pv_is("{}:POWER".format(supply), "On" if on else "Off")

    def _assert_power_supply_disabled(self, supply, disabled):
        self.ca.assert_that_pv_is_number("{}:POWER:SP.DISP".format(supply), 1 if disabled else 0)

    def _set_all_power_supply_states(self, on):
        for supply in POWER_SUPPLIES:
            self._set_power_supply_state(supply, on)

    def _assert_all_power_supplies_disabled(self, disabled):
        for supply in POWER_SUPPLIES:
            self._assert_power_supply_disabled(supply, disabled)

    def setUp(self):
        self.ca = ChannelAccess()

        # Wait for PVs that we care about to exist.
        self.ca.wait_for("COORD_01:PSUS:DISABLE:SP", timeout=30)
        self.ca.wait_for(INPUT_PV, timeout=30)
        self.ca.wait_for(ACKNOWLEDGEMENT_PV, timeout=30)
        for id in POWER_SUPPLIES:
            self.ca.wait_for("{}:POWER".format(id), timeout=30)

        self._set_input_pv(True)
        self._set_all_power_supply_states(False)

    def test_GIVEN_value_on_input_ioc_changes_THEN_coord_picks_up_the_change(self):
        def _set_and_check(ok_to_run_psus):
            self._set_input_pv(ok_to_run_psus)
            self.ca.assert_that_pv_is("COORD_01:PSUS:DISABLE:SP", "ENABLED" if ok_to_run_psus else "DISABLED")

        for ok_to_run_psus in [True, False, True]:  # Check both transitions
            _set_and_check(ok_to_run_psus)

    def test_GIVEN_all_power_supplies_off_WHEN_value_on_input_ioc_changes_THEN_power_supplies_have_their_disp_field_set(self):
        def _set_and_check_disabled_status(ok_to_run_psus):
            self._set_input_pv(ok_to_run_psus)
            self._assert_all_power_supplies_disabled(not ok_to_run_psus)

        for ok_to_run_psus in [True, False, True]:  # Check both transitions
            _set_and_check_disabled_status(ok_to_run_psus)

    def test_WHEN_any_power_supply_is_on_THEN_power_all_pv_is_high(self):

        self._set_all_power_supply_states(False)

        self.ca.assert_that_pv_is_number("COORD_01:PSUS:POWER:ANY", 0)

        for psu in POWER_SUPPLIES:
            self._set_power_supply_state(psu, True)
            self.ca.assert_that_pv_is_number("COORD_01:PSUS:POWER:ANY", 1)

            self._set_power_supply_state(psu, False)
            self.ca.assert_that_pv_is_number("COORD_01:PSUS:POWER:ANY", 0)

    def test_GIVEN_power_supplies_on_WHEN_value_on_input_ioc_changes_THEN_power_supplies_are_not_disabled_until_they_are_switched_off(self):
        self._set_all_power_supply_states(True)
        self._set_input_pv(False)
        self._assert_all_power_supplies_disabled(False)
        self._set_all_power_supply_states(False)
        self._assert_all_power_supplies_disabled(True)

    def test_GIVEN_plc_cancels_port_changeover_before_psus_are_all_switched_off_WHEN_psus_become_switched_off_THEN_they_do_not_get_disabled(self):
        self._set_all_power_supply_states(True)
        self._set_input_pv(False)
        self._assert_all_power_supplies_disabled(False)  # Power supplies not disabled because still powered on
        self._set_input_pv(True)  # PLC now cancels request to do a changeover
        self._set_all_power_supply_states(False)
        self._assert_all_power_supplies_disabled(False)

    def _set_and_check_simulated_alarm(self, supply, alarm):
        self.ca.set_pv_value("{}:POWER.SIMS".format(supply), alarm)
        self.ca.assert_pv_alarm_is("{}:POWER".format(supply), alarm)

    # Using a context manager to put PVs into alarm means they don't accidentally get left in alarm if the test fails
    @contextmanager
    def _put_power_supply_into_alarm(self, supply):
        try:
            self._set_and_check_simulated_alarm(supply, self.ca.ALARM_INVALID)
            yield
        finally:
            self._set_and_check_simulated_alarm(supply, self.ca.ALARM_NONE)

    def test_GIVEN_a_power_supply_is_in_alarm_THEN_the_power_any_pv_is_also_in_alarm(self):
        for supply in POWER_SUPPLIES:
            with self._put_power_supply_into_alarm(supply):
                self.ca.assert_pv_alarm_is("COORD_01:PSUS:POWER:ANY", self.ca.ALARM_INVALID)
            self.ca.assert_pv_alarm_is("COORD_01:PSUS:POWER:ANY", self.ca.ALARM_NONE)

    def test_GIVEN_a_power_supply_is_in_alarm_THEN_the_power_any_pv_reports_that_psus_are_active(self):
        for supply in POWER_SUPPLIES:
            with self._put_power_supply_into_alarm(supply):
                self.ca.assert_that_pv_is_number("COORD_01:PSUS:POWER:ANY", 1)
            self.ca.assert_that_pv_is_number("COORD_01:PSUS:POWER:ANY", 0)

    def test_GIVEN_changeover_initiated_WHEN_power_supplies_off_THEN_acknowledgement_pv_true(self):
        self._set_all_power_supply_states(False)
        self._set_input_pv(False)

        self.ca.assert_that_pv_is_number(ACKNOWLEDGEMENT_PV, 1)

        self._set_input_pv(True)  # Some time later the PLC sends signal to say it has finished the changeover sequence
        self.ca.assert_that_pv_is_number(ACKNOWLEDGEMENT_PV, 0)
