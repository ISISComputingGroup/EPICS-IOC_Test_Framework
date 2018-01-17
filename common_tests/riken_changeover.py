import unittest
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager

from utils.channel_access import ChannelAccess


class RikenChangeover(unittest.TestCase):
    """
    Tests for a riken changeover.

    This class is inherited by the riken port changeover tests and also the RB2 mode change tests as they are very
    similar (just the PSUs that they look at / control are different)
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_input_pv(self):
        pass

    @abstractmethod
    def get_acknowledgement_pv(self):
        pass

    @abstractmethod
    def get_power_supplies(self):
        pass

    @abstractmethod
    def get_prefix(self):
        pass

    def _set_input_pv(self, ok_to_run_psus):
        self.ca.set_pv_value("{}:SP".format(self.get_input_pv()), 1 if ok_to_run_psus else 0)

    def _set_power_supply_state(self, supply, on):
        self.ca.set_pv_value("{}:POWER:SP".format(supply), 1 if on else 0)
        self.ca.assert_that_pv_is("{}:POWER".format(supply), "On" if on else "Off")

    def _assert_power_supply_disabled(self, supply, disabled):
        self.ca.assert_that_pv_is_number("{}:POWER:SP.DISP".format(supply), 1 if disabled else 0)

    def _set_all_power_supply_states(self, on):
        for supply in self.get_power_supplies():
            self._set_power_supply_state(supply, on)

    def _assert_all_power_supplies_disabled(self, disabled):
        for supply in self.get_power_supplies():
            self._assert_power_supply_disabled(supply, disabled)

    def setUp(self):
        self.ca = ChannelAccess()

        # Wait for PVs that we care about to exist.
        self.ca.wait_for("{}:PSUS:DISABLE".format(self.get_prefix()), timeout=30)
        self.ca.wait_for(self.get_input_pv(), timeout=30)
        self.ca.wait_for(self.get_acknowledgement_pv(), timeout=30)
        for id in self.get_power_supplies():
            self.ca.wait_for("{}:POWER".format(id), timeout=30)

        self._set_input_pv(True)
        self._set_all_power_supply_states(False)

    def test_GIVEN_value_on_input_ioc_changes_THEN_coord_picks_up_the_change(self):
        def _set_and_check(ok_to_run_psus):
            self._set_input_pv(ok_to_run_psus)
            self.ca.assert_that_pv_is("{}:PSUS:DISABLE".format(self.get_prefix()),
                                      "ENABLED" if ok_to_run_psus else "DISABLED")

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

        self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_prefix()), 0)

        for psu in self.get_power_supplies():
            self._set_power_supply_state(psu, True)
            self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_prefix()), 1)

            self._set_power_supply_state(psu, False)
            self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_prefix()), 0)

    def test_GIVEN_power_supplies_on_WHEN_value_on_input_ioc_changes_THEN_power_supplies_are_not_disabled_until_they_are_switched_off(self):
        self._set_all_power_supply_states(True)
        self._set_input_pv(False)
        self._assert_all_power_supplies_disabled(False)
        self._set_all_power_supply_states(False)
        self._assert_all_power_supplies_disabled(True)

    def test_GIVEN_plc_cancels_changeover_before_psus_are_all_switched_off_WHEN_psus_become_switched_off_THEN_they_do_not_get_disabled(self):
        self._set_all_power_supply_states(True)
        self._set_input_pv(False)
        self._assert_all_power_supplies_disabled(False)  # Power supplies not disabled because still powered on
        self._set_input_pv(True)  # PLC now cancels request to do a changeover
        self._set_all_power_supply_states(False)
        self._assert_all_power_supplies_disabled(False)

    # Using a context manager to put PVs into alarm means they don't accidentally get left in alarm if the test fails
    @contextmanager
    def _put_power_supply_into_alarm(self, supply):
        def _set_and_check_simulated_alarm(supply, alarm):
            self.ca.set_pv_value("{}:POWER.SIMS".format(supply), alarm)
            self.ca.assert_pv_alarm_is("{}:POWER".format(supply), alarm)

        try:
            _set_and_check_simulated_alarm(supply, self.ca.ALARM_INVALID)
            yield
        finally:
            _set_and_check_simulated_alarm(supply, self.ca.ALARM_NONE)

    def test_GIVEN_a_power_supply_is_in_alarm_THEN_the_power_any_pv_is_also_in_alarm(self):
        for supply in self.get_power_supplies():
            with self._put_power_supply_into_alarm(supply):
                self.ca.assert_pv_alarm_is("{}:PSUS:POWER".format(self.get_prefix()), self.ca.ALARM_INVALID)
            self.ca.assert_pv_alarm_is("{}:PSUS:POWER".format(self.get_prefix()), self.ca.ALARM_NONE)

    def test_GIVEN_a_power_supply_is_in_alarm_THEN_the_power_any_pv_reports_that_psus_are_active(self):
        for supply in self.get_power_supplies():
            with self._put_power_supply_into_alarm(supply):
                self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_prefix()), 1)
            self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_prefix()), 0)

    def test_GIVEN_changeover_initiated_WHEN_power_supplies_off_THEN_acknowledgement_pv_true(self):
        self._set_all_power_supply_states(False)
        self._set_input_pv(False)

        self.ca.assert_that_pv_is_number(self.get_acknowledgement_pv(), 1)

        self._set_input_pv(True)  # Some time later the PLC sends signal to say it has finished the changeover sequence
        self.ca.assert_that_pv_is_number(self.get_acknowledgement_pv(), 0)
