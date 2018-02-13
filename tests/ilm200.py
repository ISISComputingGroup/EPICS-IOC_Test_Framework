import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class Ilm200Tests(unittest.TestCase):
    """
    Tests for the Ilm200 IOC.
    """
    DEFAULT_SCAN_RATE = 1
    SLOW = "Slow"
    FAST = "Fast"
    LEVEL_TOLERANCE = 0.1

    FULL = 100.0
    LOW = 10.0
    FILL = 5.0

    RATE = "RATE"
    LEVEL = "LEVEL"
    TYPE = "TYPE"
    CURRENT = "CURR"

    @staticmethod
    def channel_range():
        number_of_channels = 3
        starting_index = 1
        return range(starting_index, starting_index + number_of_channels)

    def helium_channels(self):
        for i in self.channel_range():
            if self.ca.get_pv_value(self.ch_pv(i, self.TYPE)) != "Nitrogen":
                yield i

    @staticmethod
    def ch_pv(channel, pv):
        return "CH{}:{}".format(channel, pv)

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ilm200")
        self.ca = ChannelAccess(device_prefix="ILM200_01")
        self.ca.wait_for("VERSION", timeout=30)
        self._lewis.backdoor_set_on_device("cycle", False)

    def set_level_via_backdoor(self, channel, level):
        self._lewis.backdoor_command(["device", "set_level", str(channel), str(level)])

    def set_helium_current_via_backdoor(self, channel, is_on):
        self._lewis.backdoor_command(["device", "set_helium_current", str(channel), str(is_on)])

    def check_state(self, channel, level, is_filling, is_low):
        self.ca.assert_that_pv_is_number(self.ch_pv(channel, self.LEVEL), level, self.LEVEL_TOLERANCE)
        self.ca.assert_that_pv_is(self.ch_pv(channel, "FILLING"), "Filling" if is_filling else "Not filling")
        self.ca.assert_that_pv_is(self.ch_pv(channel, "LOW"), "Low" if is_low else "Not low")

    def test_GIVEN_ilm200_THEN_has_version(self):
        self.ca.assert_that_pv_is_not("VERSION", "")
        self.ca.assert_pv_alarm_is("VERSION", ChannelAccess.ALARM_NONE)

    def test_GIVEN_ilm200_THEN_each_channel_has_type(self):
        for i in self.channel_range():
            self.ca.assert_that_pv_is_not(self.ch_pv(i, self.TYPE), "Not in use")
            self.ca.assert_pv_alarm_is(self.ch_pv(i, self.TYPE), ChannelAccess.ALARM_NONE)

    def test_GIVEN_ilm_200_THEN_can_read_level(self):
        for i in self.channel_range():
            self.ca.assert_pv_alarm_is(self.ch_pv(i, self.LEVEL), ChannelAccess.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm_200_WHEN_level_set_on_device_THEN_reported_level_matches_set_level(self):
        for i in self.channel_range():
            expected_level = i*12.3
            self.set_level_via_backdoor(i, expected_level)
            self.ca.assert_that_pv_is_number(self.ch_pv(i, self.LEVEL), expected_level, self.LEVEL_TOLERANCE)

    @skipIf(IOCRegister.uses_rec_sim, "No dynamic behaviour recsim")
    def test_GIVEN_ilm_200_WHEN_is_cycling_THEN_channel_levels_change_over_time(self):
        self._lewis.backdoor_set_on_device("cycle", True)
        for i in self.channel_range():
            def not_equal(a, b):
                tolerance = self.LEVEL_TOLERANCE
                return abs(a-b)/(a+b+tolerance) > tolerance
            self.ca.assert_pv_value_over_time(self.ch_pv(i, self.LEVEL), 2*Ilm200Tests.DEFAULT_SCAN_RATE, not_equal)

    def test_GIVEN_ilm200_channel_WHEN_rate_change_requested_THEN_rate_changed(self):
        for i in self.channel_range():
            initial_rate = self.ca.get_pv_value(self.ch_pv(i, self.RATE))
            alternate_rate = self.SLOW if initial_rate == self.FAST else self.SLOW

            self.ca.assert_setting_setpoint_sets_readback(alternate_rate, self.ch_pv(i, self.RATE))
            self.ca.assert_setting_setpoint_sets_readback(initial_rate, self.ch_pv(i, self.RATE))

    def test_GIVEN_ilm200_channel_WHEN_rate_set_to_current_value_THEN_rate_unchanged(self):
        for i in self.channel_range():
            self.ca.assert_setting_setpoint_sets_readback(self.ca.get_pv_value(self.ch_pv(i, self.RATE)),
                                                          self.ch_pv(i, self.RATE))

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_full_THEN_not_filling_and_not_low(self):
        for i in self.channel_range():
            level = self.FULL
            self.set_level_via_backdoor(i, level)
            self.check_state(i, level, False, False)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_low_but_auto_fill_not_triggered_THEN_not_filling_and_low(self):
        for i in self.channel_range():
            level = self.LOW - (self.LOW - self.FILL)/2  # Somewhere between fill and low
            self.set_level_via_backdoor(i, level)
            self.check_state(i, level, False, True)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_low_but_and_auto_fill_triggered_THEN_filling_and_low(self):
        for i in self.channel_range():
            level = self.FILL/2
            self.set_level_via_backdoor(i, level)
            self.check_state(i, level, True, True)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_low_THEN_alarm(self):
        for i in self.channel_range():
            level = self.FILL/2
            self.set_level_via_backdoor(i, level)
            self.ca.assert_pv_alarm_is(self.ch_pv(i, "LOW"), self.ca.ALARM_MINOR)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door in recsim")
    def test_GIVEN_helium_channel_WHEN_helium_current_set_on_THEN_ioc_reports_current(self):
        for i in self.helium_channels():
            self.set_helium_current_via_backdoor(i, True)
            self.ca.assert_that_pv_is(self.ch_pv(i, self.CURRENT), "On")

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door in recsim")
    def test_GIVEN_helium_channel_WHEN_helium_current_set_off_THEN_ioc_reports_no_current(self):
        for i in self.helium_channels():
            self.set_helium_current_via_backdoor(i, False)
            self.ca.assert_that_pv_is(self.ch_pv(i, self.CURRENT), "Off")
