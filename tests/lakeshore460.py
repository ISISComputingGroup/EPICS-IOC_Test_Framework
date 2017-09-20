import unittest
from unittest import skipIf
from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from utils.ioc_launcher import IOCRegister

class UnitStrings(object):
    GAUSS = "G"
    TESLA = "T"
    ON = "ON"
    OFF = "OFF"
    AC = "AC"
    DC = "DC"
    PEAK = "PEAK"
    RMS = "RMS"


class UnitFlags(object):
    GAUSS = 0
    TESLA = 1
    ON = 1
    OFF = 0
    AC = 0
    DC = 1
    PEAK = 1
    RMS = 0

class Lakeshore460Tests(unittest.TestCase):
    """
    Tests for the Lakeshore460.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("lakeshore460")
        self.ca = ChannelAccess(default_timeout=30)
        self.ca.wait_for("LKSH460_01:IDN")

    def _set_IDN(self, expected_idn):
        self._lewis.backdoor_set_on_device("idn", expected_idn)
        self._ioc.set_simulated_value("LKSH460_01:SIM:IDN", expected_idn)

    def _set_max_reading(self, expected_max_reading):
        self._lewis.backdoor_set_on_device("max_reading", expected_max_reading)
        self._ioc.set_simulated_value("LKSH460_01:SIM:MAXREADING", expected_max_reading)

    def _set_unit(self, expected_unit):
        expected_channels = {"X": expected_unit, "Y": expected_unit, "Z": expected_unit, "V": expected_unit}
        for channel, unit in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:UNIT:SP".format(channel), unit)

    def _set_total_fields(self, expected_total_fields):
        self._lewis.backdoor_set_on_device("total_fields", expected_total_fields)
        self._ioc.set_simulated_value("LKSH460_01:SIM:ALLFIELDS", expected_total_fields)

    def _set_rel_mode_reading(self, expected_rel_mode_reading):
        self._lewis.backdoor_set_on_device("rel_mode_reading", expected_rel_mode_reading)
        self._ioc.set_simulated_value("LKSH460_01:SIM:RELMODEREADING", expected_rel_mode_reading)

    def _set_magnetic_field_reading(self, expected_magnetic_field_reading):
        self._lewis.backdoor_set_on_device("magnetic_field_reading", expected_magnetic_field_reading)
        self._ioc.set_simulated_value("LKSH460_01:SIM:FIELDREADING", expected_magnetic_field_reading)

    def test_GIVEN_idn_set_WHEN_read_THEN_idn_is_as_expected(self):
        expected_idn = "000000000000000000111111111111111111151"
        self._set_IDN(expected_idn)
        self.ca.set_pv_value("LKSH460_01:IDN.PROC", 1)
        self.ca.assert_that_pv_is("LKSH460_01:IDN", expected_idn)

    def test_GIVEN_unit_set_for_a_channel_WHEN_read_THEN_unit_is_as_expected_for_channel(self):
        expected_unit_str = UnitStrings.TESLA
        expected_unit_flag = UnitFlags.TESLA
        self._set_unit(expected_unit_flag)
        expected_channels = {"X": expected_unit_str, "Y": expected_unit_str, "Z": expected_unit_str,
                             "V": expected_unit_str}
        for channel, unit in expected_channels.iteritems():
            self.ca.assert_that_pv_is("LKSH460_01:{0}:UNIT".format(channel), unit)

    def test_GIVEN_output_status_set_for_a_channel_WHEN_read_THEN_output_STATUS_is_as_expected_for_channel(self):
        expected_output_status_flag = UnitFlags.ON
        expected_channels = {"X": expected_output_status_flag, "Y": expected_output_status_flag,
                             "Z": expected_output_status_flag, "V": expected_output_status_flag}
        for channel, output_status in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:OUTPUTSTATUS:SP".format(channel), output_status)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:OUTPUTSTATUS".format(channel), UnitStrings.ON)

    def test_GIVEN_output_mode_set_for_a_channel_WHEN_read_THEN_output_mode_is_as_expected_for_channel(self):
        expected_output_mode_flag = UnitFlags.DC
        expected_channels = {"X": expected_output_mode_flag, "Y": expected_output_mode_flag,
                             "Z": expected_output_mode_flag, "V": expected_output_mode_flag}
        for channel, output_mode in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:OUTPUTMODE:SP".format(channel), output_mode)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:OUTPUTMODE".format(channel), UnitStrings.DC)

    def test_GIVEN_prms_set_for_a_channel_WHEN_read_THEN_prms_is_as_expected_for_set_channel(self):
        expected_prms_status_flag = UnitFlags.PEAK
        expected_channels = {"X": expected_prms_status_flag, "Y": expected_prms_status_flag,
                             "Z": expected_prms_status_flag, "V": expected_prms_status_flag}
        for channel, prms_status in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:PRMS:SP".format(channel), prms_status)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:PRMS".format(channel), UnitStrings.PEAK)

    def test_GIVEN_display_filter_set_for_channel_WHEN_read_THEN_display_filter_is_as_expected_for_channel(self):
        expected_display_filter_flag = UnitFlags.ON
        expected_channels = {"X": expected_display_filter_flag, "Y": expected_display_filter_flag,
                             "Z": expected_display_filter_flag, "V": expected_display_filter_flag}
        for channel, display_filter in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:FILTER:SP".format(channel), display_filter)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:FILTER".format(channel), UnitStrings.ON)

    def test_GIVEN_relative_mode_set_for_channel_WHEN_read_THEN_relative_mode_is_as_expected_for_set_channel(self):
        expected_relative_mode_flag = UnitFlags.ON
        expected_channels = {"X": expected_relative_mode_flag, "Y": expected_relative_mode_flag,
                             "Z": expected_relative_mode_flag, "V": expected_relative_mode_flag}
        for channel, display_filter in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:RELMODE:SP".format(channel), display_filter)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:RELMODE".format(channel), UnitStrings.ON)

    def test_GIVEN_max_hold_set_WHEN_read_THEN_max_hold_is_as_expected(self):
        expected_max_hold_flag = UnitFlags.ON
        expected_channels = {"X": expected_max_hold_flag, "Y": expected_max_hold_flag,
                             "Z": expected_max_hold_flag, "V": expected_max_hold_flag}
        for channel, max_hold in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:MAXHOLD:SP".format(channel), max_hold)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:MAXHOLD".format(channel), UnitStrings.ON)

    def test_GIVEN_auto_range_set_WHEN_read_THEN_auto_range_is_as_expected(self):
        expected_auto_range_flag = UnitFlags.ON
        expected_channels = {"X": expected_auto_range_flag, "Y": expected_auto_range_flag,
                             "Z": expected_auto_range_flag, "V": expected_auto_range_flag}
        for channel, range in expected_channels.iteritems():
            self.ca.set_pv_value("LKSH460_01:{0}:AUTO:SP".format(channel), range)
            self.ca.assert_that_pv_is("LKSH460_01:{0}:AUTO".format(channel), UnitStrings.ON)

    # def test_GIVEN_source_set_WHEN_read_THEN_source_is_as_expected(self):
    #     expected_source = 3
    #     self.ca.set_pv_value("LKSH460_01:SOURCE:SP", expected_source)
    #     self.ca.assert_that_pv_is("LKSH460_01:SOURCE", "XZ")

    def test_GIVEN_filter_window_set_for_a_channel_WHEN_read_THEN_filter_window_is_as_expected_AND_within_range(self):
        # expected_window_percentage = [1, 11, 10, 22]
        # alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE,
        #                ChannelAccess.ALARM_MAJOR]
        channels = ["X", "Y", "Z", "V"]
        sample_data = {1: ChannelAccess.ALARM_NONE, 11: ChannelAccess.ALARM_MAJOR, 10: ChannelAccess.ALARM_NONE,
                       22: ChannelAccess.ALARM_MAJOR}

        self.ca.set_pv_value("LKSH460_01:X:FWIN:SP", 5)
        self.ca.assert_that_pv_is("LKSH460_01:X:FWIN", 5)
               # self.ca.assert_pv_alarm_is("LKSH460_01:X:FWIN", A)





