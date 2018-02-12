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

    @staticmethod
    def channel_range():
        number_of_channels = 3
        starting_index = 1
        return range(starting_index, starting_index + number_of_channels)

    @staticmethod
    def ch_pv(channel, pv):
        return "CH{}:{}".format(channel, pv)

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ilm200")
        self.ca = ChannelAccess(device_prefix="ILM200_01")
        self.ca.wait_for("VERSION", timeout=30)

    def set_level_via_backdoor(self, channel, level):
        self._lewis.backdoor_command(["device", "set_level", str(channel), str(level)])

    def check_state(self, channel, level, is_filling, is_low):
        self.ca.assert_that_pv_is_number(self.ch_pv(channel, "LEVEL"), level, 0.01)
        self.ca.assert_that_pv_is(self.ch_pv(channel, "FILLING"), "Filling" if is_filling else "Not filling")
        self.ca.assert_that_pv_is(self.ch_pv(channel, "LOW"), "Low" if is_low else "Not low")

    def test_GIVEN_ilm200_THEN_has_version(self):
        self.ca.assert_that_pv_is_not("VERSION", "")
        self.ca.assert_pv_alarm_is("VERSION", ChannelAccess.ALARM_NONE)

    def test_GIVEN_ilm200_THEN_each_channel_has_type(self):
        for i in self.channel_range():
            self.ca.assert_that_pv_is_not(self.ch_pv(i, "TYPE"), "Not in use")
            self.ca.assert_pv_alarm_is(self.ch_pv(i, "TYPE"), ChannelAccess.ALARM_NONE)

    def test_GIVEN_ilm_200_THEN_can_access_levels_for_three_channels(self):
        for i in self.channel_range():
            self.ca.assert_pv_alarm_is(self.ch_pv(i, "LEVEL"), ChannelAccess.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm_200_WHEN_level_set_on_device_THEN_reported_level_matches_set_level(self):
        self._lewis.backdoor_set_on_device("cycle", False)
        for i in self.channel_range():
            expected_level = i*12.34
            self.set_level_via_backdoor(i, expected_level)
            self.ca.assert_that_pv_is_number(self.ch_pv(i, "LEVEL"), expected_level, 0.01)

    @skipIf(IOCRegister.uses_rec_sim, "No dynamic behaviour recsim")
    def test_GIVEN_ilm_200_THEN_channel_levels_change_over_time(self):
        for i in self.channel_range():
            def not_equal(a, b):
                tolerance = 0.01
                return abs(a-b)/(a+b+tolerance) > tolerance
            self.ca.assert_pv_value_over_time(self.ch_pv(i, "LEVEL"), 2*Ilm200Tests.DEFAULT_SCAN_RATE, not_equal)

    def test_GIVEN_ilm200_channel_WHEN_rate_change_requested_THEN_rate_changed(self):
        for i in self.channel_range():
            initial_rate = self.ca.get_pv_value(self.ch_pv(i, "RATE"))
            alternate_rate = self.SLOW if initial_rate==self.FAST else self.SLOW

            self.ca.assert_setting_setpoint_sets_readback(alternate_rate, self.ch_pv(i, "RATE"))
            self.ca.assert_setting_setpoint_sets_readback(initial_rate, self.ch_pv(i, "RATE"))

    def test_GIVEN_ilm200_channel_WHEN_rate_set_to_current_value_THEN_rate_unchanged(self):
        for i in self.channel_range():
            self.ca.assert_setting_setpoint_sets_readback(self.ca.get_pv_value(self.ch_pv(i, "RATE")),
                                                          self.ch_pv(i, "RATE"))

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_full_THEN_not_filling_and_not_low(self):
        self._lewis.backdoor_set_on_device("cycle", False)
        for i in self.channel_range():
            level = 100.0
            self.set_level_via_backdoor(i, level)
            self.check_state(i, level, False, False)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_low_but_auto_fill_not_triggered_THEN_not_filling_and_low(self):
        self._lewis.backdoor_set_on_device("cycle", False)
        for i in self.channel_range():
            level = 7.5
            self.set_level_via_backdoor(i, level)
            self.check_state(i, level, False, True)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_low_but_and_auto_fill_triggered_THEN_filling_and_low(self):
        self._lewis.backdoor_set_on_device("cycle", False)
        for i in self.channel_range():
            level = 2.5
            self.set_level_via_backdoor(i, level)
            self.check_state(i, level, True, True)

    @skipIf(IOCRegister.uses_rec_sim, "Cannot do back door of dynamic behaviour in recsim")
    def test_GIVEN_ilm200_WHEN_channel_low_THEN_alarm(self):
        self._lewis.backdoor_set_on_device("cycle", False)
        for i in self.channel_range():
            level = 2.5
            self.set_level_via_backdoor(i, level)
            self.ca.assert_pv_alarm_is(self.ch_pv(i, "LOW"), self.ca.ALARM_MINOR)