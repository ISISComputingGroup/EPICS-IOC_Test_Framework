import six
from abc import ABCMeta, abstractmethod
from utils.channel_access import ChannelAccess

try:
    from contextlib import ExitStack  # PY3
except ImportError:
    from contextlib2 import ExitStack  # PY2


@six.add_metaclass(ABCMeta)
class RikenChangeover(object):
    """
    Tests for a riken changeover.

    This class is inherited by the riken port changeover tests and also the RB2 mode change tests as they are very
    similar (just the PSUs that they look at / control are different)
    """
    @abstractmethod
    def get_input_pv(self):
        return ""

    @abstractmethod
    def get_acknowledgement_pv(self):
        return ""

    @abstractmethod
    def get_power_supplies(self):
        return []

    @abstractmethod
    def get_coord_prefix(self):
        return ""

    @abstractmethod
    def get_prefix(self):
        return ""

    def _set_input_pv(self, ok_to_run_psus):
        self.ca.set_pv_value("{}:SIM".format(self.get_input_pv()), 1 if ok_to_run_psus else 0)

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
        self.ca = ChannelAccess(device_prefix=self.get_prefix(), default_timeout=10)

        # Wait for PVs that we care about to exist.
        self.ca.assert_that_pv_exists("{}:PSUS:DISABLE".format(self.get_coord_prefix()), timeout=30)
        self.ca.assert_that_pv_exists(self.get_input_pv())
        self.ca.assert_that_pv_exists(self.get_acknowledgement_pv())
        for id in self.get_power_supplies():
            self.ca.assert_that_pv_exists("{}:POWER".format(id))

        self._set_input_pv(True)
        self._set_all_power_supply_states(False)

    def test_GIVEN_value_on_input_ioc_changes_THEN_coord_psus_disable_pv_updates_with_the_same_value(self):
        def _set_and_check(ok_to_run_psus):
            self._set_input_pv(ok_to_run_psus)
            self.ca.assert_that_pv_is("{}:PSUS:DISABLE".format(self.get_coord_prefix()),
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

        self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_coord_prefix()), 0)

        for psu in self.get_power_supplies():
            self._set_power_supply_state(psu, True)
            self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_coord_prefix()), 1)

            self._set_power_supply_state(psu, False)
            self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_coord_prefix()), 0)

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

    def test_GIVEN_a_power_supply_is_in_alarm_THEN_the_power_any_pv_is_also_in_alarm(self):
        for supply in self.get_power_supplies():
            with self.ca.put_simulated_record_into_alarm("{}:POWER".format(supply), self.ca.Alarms.INVALID):
                self.ca.assert_that_pv_alarm_is("{}:PSUS:POWER".format(self.get_coord_prefix()), self.ca.Alarms.INVALID)
            self.ca.assert_that_pv_alarm_is("{}:PSUS:POWER".format(self.get_coord_prefix()), self.ca.Alarms.NONE)

    def test_GIVEN_all_power_supply_are_in_alarm_THEN_the_power_any_pv_is_also_in_alarm(self):
        with ExitStack() as stack:
            for supply in self.get_power_supplies():
                stack.enter_context(
                    self.ca.put_simulated_record_into_alarm("{}:POWER".format(supply), self.ca.Alarms.INVALID)
                )
            self.ca.assert_that_pv_alarm_is("{}:PSUS:POWER".format(self.get_coord_prefix()), self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is("{}:PSUS:POWER".format(self.get_coord_prefix()), self.ca.Alarms.NONE)

    def test_GIVEN_a_power_supply_is_in_alarm_THEN_the_power_any_pv_reports_that_psus_are_active(self):
        for supply in self.get_power_supplies():
            with self.ca.put_simulated_record_into_alarm("{}:POWER".format(supply), self.ca.Alarms.INVALID):
                self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_coord_prefix()), 1)
            self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_coord_prefix()), 0)

    def test_GIVEN_all_power_supply_are_in_alarm_THEN_the_power_any_pv_reports_that_psus_are_active(self):
        with ExitStack() as stack:
            for supply in self.get_power_supplies():
                stack.enter_context(
                    self.ca.put_simulated_record_into_alarm("{}:POWER".format(supply), self.ca.Alarms.INVALID)
                )
            self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_coord_prefix()), 1)
        self.ca.assert_that_pv_is_number("{}:PSUS:POWER".format(self.get_coord_prefix()), 0)

    def test_GIVEN_changeover_initiated_WHEN_power_supplies_off_THEN_acknowledgement_pv_true(self):
        self._set_all_power_supply_states(False)
        self._set_input_pv(False)

        self.ca.assert_that_pv_is_number(self.get_acknowledgement_pv(), 1)

        self._set_input_pv(True)  # Some time later the PLC sends signal to say it has finished the changeover sequence
        self.ca.assert_that_pv_is_number(self.get_acknowledgement_pv(), 0)

    def test_GIVEN_changeover_sequence_completes_THEN_power_supplies_are_reenabled_after_sequence(self):
        self._set_all_power_supply_states(True)
        self._set_input_pv(False)
        self._assert_all_power_supplies_disabled(False)  # Power supplies not disabled because still powered on
        self._set_all_power_supply_states(False)  # Power supplies now switched off so changeover can continue
        self._assert_all_power_supplies_disabled(True)  # All power supplies are now disabled
        self.ca.assert_that_pv_is(self.get_acknowledgement_pv(), 1)
        self._set_input_pv(True)  # Some time later, changeover is finished
        self._assert_all_power_supplies_disabled(False)  # Power supplies should now be reenabled
