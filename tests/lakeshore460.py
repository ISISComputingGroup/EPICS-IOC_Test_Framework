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
    AUTORANGEON = "Auto Range " + ON
    AUTORANGEOFF = "Auto Range " + OFF

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
        self.ca.set_pv_value("LKSH460_01:UNIT:SP", expected_unit)

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

    def test_GIVEN_unit_set_WHEN_read_THEN_unit_is_as_expected(self):
        expected_unit_str = UnitStrings.TESLA
        expected_unit_flag = UnitFlags.TESLA
        self._set_unit(expected_unit_flag)
        self.ca.assert_that_pv_is("LKSH460_01:UNIT", expected_unit_str)

    def test_GIVEN_output_status_set_WHEN_read_THEN_output_STATUS_is_as_expected(self):
        expected_output_status_flag = UnitFlags.ON
        self.ca.set_pv_value("LKSH460_01:OUTPUTSTATUS:SP", expected_output_status_flag)
        self.ca.assert_that_pv_is("LKSH460_01:OUTPUTSTATUS", UnitStrings.ON)

    def test_GIVEN_output_mode_set_WHEN_read_THEN_output_mode_is_as_expected(self):
        expected_output_status_flag = UnitFlags.DC
        self.ca.set_pv_value("LKSH460_01:OUTPUTMODE:SP", expected_output_status_flag)
        self.ca.assert_that_pv_is("LKSH460_01:OUTPUTMODE", UnitStrings.DC)

    def test_GIVEN_prms_set_WHEN_read_THEN_prms_is_as_expected(self):
        expected_prms_status_flag = UnitFlags.PEAK
        self.ca.set_pv_value("LKSH460_01:PRMS:SP", expected_prms_status_flag)
        self.ca.assert_that_pv_is("LKSH460_01:PRMS", UnitStrings.PEAK)

    def test_GIVEN_display_filter_set_WHEN_read_THEN_display_filter_is_as_expected(self):
        expected_display_filter_flag = UnitFlags.ON
        self.ca.set_pv_value("LKSH460_01:FILTER:SP", expected_display_filter_flag)
        self.ca.assert_that_pv_is("LKSH460_01:FILTER", UnitStrings.ON)

    def test_GIVEN_relative_mode_set_WHEN_read_THEN_relative_mode_is_as_expected(self):
        expected_relative_mode_flag = UnitFlags.ON
        self.ca.set_pv_value("LKSH460_01:RELMODE:SP", expected_relative_mode_flag)
        self.ca.assert_that_pv_is("LKSH460_01:RELMODE", UnitStrings.ON)

    def test_GIVEN_max_hold_set_WHEN_read_THEN_max_hold_is_as_expected(self):
        expected_max_hold_flag = UnitFlags.ON
        self.ca.set_pv_value("LKSH460_01:MAXHOLD:SP", expected_max_hold_flag)
        self.ca.assert_that_pv_is("LKSH460_01:MAXHOLD", UnitStrings.ON)

    def test_GIVEN_auto_range_set_WHEN_read_THEN_auto_range_is_as_expected(self):
        expected_auto_range_flag = UnitFlags.ON
        self.ca.set_pv_value("LKSH460_01:AUTO:SP", expected_auto_range_flag)
        self.ca.assert_that_pv_is("LKSH460_01:AUTO", UnitStrings.AUTORANGEON)

    def test_GIVEN_all_fields_set_WHEN_read_THEN_all_fields_is_as_expected(self):
        expected_total_fields = 8.3
        self._set_total_fields(expected_total_fields)
        self.ca.assert_that_pv_is("LKSH460_01:ALLFIELDS", expected_total_fields)

    def test_GIVEN_source_set_WHEN_read_THEN_source_is_as_expected(self):
        expected_source = 3
        self.ca.set_pv_value("LKSH460_01:SOURCE:SP", expected_source)
        self.ca.assert_that_pv_is("LKSH460_01:SOURCE", "XZ")

    def test_GIVEN_channel_set_WHEN_read_THEN_channel_is_as_expected(self):
        inputs = [1, 2, 3 ,4]
        expected_range = ["Channel X", "Channel Y", "Channel Z", "Vector Magnitude Channel"]
        for input, output in zip(inputs, expected_range):
            self.ca.set_pv_value("LKSH460_01:CHANNEL:SP", input)
            self.ca.assert_that_pv_is("LKSH460_01:CHANNEL", output)

    def test_GIVEN_filter_window_set_WHEN_read_THEN_filter_window_is_as_expected_AND_within_range(self):
        expected_window_percentage = [1,11, 10, 22]
        alarm_state = [ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR]
        for input, output in zip(expected_window_percentage, alarm_state):
            self.ca.set_pv_value("LKSH460_01:FWIN:SP", input)
            self.ca.assert_that_pv_is("LKSH460_01:FWIN", input)
            self.ca.assert_pv_alarm_is("LKSH460_01:FWIN", output)

    def test_GIVEN_filter_points_set_WHEN_read_THEN_filter_points_is_as_expected_AND_within_range(self):
        expected_filter_points = [70, 64, 65, 2]
        alarm_state = [ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE, ChannelAccess.ALARM_MAJOR, ChannelAccess.ALARM_NONE]
        for input, output in zip(expected_filter_points, alarm_state):
            self.ca.set_pv_value("LKSH460_01:FNUM:SP", input)
            self.ca.assert_that_pv_is("LKSH460_01:FNUM", input)
            self.ca.assert_pv_alarm_is("LKSH460_01:FNUM", output)

    def test_GIVEN_range_set_manually_WHEN_read_THEN_range_is_as_expected(self):
        inputs = [0,1,2,3]
        expected_range = ["First Range", "Second Range", "Third Range", "Fourth Range"]
        for input, output in zip(inputs, expected_range):
            self.ca.set_pv_value("LKSH460_01:RANGE:SP", input)
            self.ca.assert_that_pv_is("LKSH460_01:RANGE", output)

    def test_GIVEN_max_reading_set_WHEN_read_THEN_max_reading_is_as_expected(self):
        expected_max_reading = 500
        self._set_max_reading(expected_max_reading)
        self.ca.assert_that_pv_is("LKSH460_01:MAXREADING", expected_max_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_max_reading_unit_set_WHEN_read_THEN_max_reading_unit_is_as_expected(self):
        inputs = [0, 1, 2, 3]
        expected_unit = ["uG", "mG", "G", "kG"]
        for input, output in zip(inputs, expected_unit):
            self.ca.set_pv_value("LKSH460_01:MAX:MULTIPLIER", input)
            self.ca.assert_that_pv_is("LKSH460_01:MAXREADING.EGU", output)

    def test_GIVEN_relative_mode_set_point_set_WHEN_read_THEN_relative_mode_set_point_is_as_expected(self):
        expected_rel_set_point = 4132
        self.ca.set_pv_value("LKSH460_01:RELSMODE:SP", expected_rel_set_point)
        self.ca.assert_that_pv_is("LKSH460_01:RELSMODE", expected_rel_set_point)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_relative_mode_set_point_unit_set_WHEN_read_THEN_relative_mode_set_point_unit_is_as_expected(self):
        inputs = [0, 1, 2, 3]
        expected_unit = ["uG", "mG", "G", "kG"]
        for input, output in zip(inputs, expected_unit):
            self.ca.set_pv_value("LKSH460_01:RELS:MULTIPLIER", input)
            self.ca.assert_that_pv_is("LKSH460_01:RELSMODE.EGU", output)

    def test_GIVEN_relative_mode_reading_set_WHEN_read_THEN_relative_mode_reading_is_as_expected(self):
        expected_rel_mode_reading = 500
        self._set_rel_mode_reading(expected_rel_mode_reading)
        self.ca.assert_that_pv_is("LKSH460_01:RELMODEREADING", expected_rel_mode_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_relative_mode_reading_unit_set_WHEN_read_THEN_relative_mode_reading_unit_is_as_expected(self):
        inputs = [0, 1, 2, 3]
        expected_unit = ["uG", "mG", "G", "kG"]
        for input, output in zip(inputs, expected_unit):
            self.ca.set_pv_value("LKSH460_01:RELRM:MULTIPLIER", input)
            self.ca.assert_that_pv_is("LKSH460_01:RELMODEREADING.EGU", output)

    def test_GIVEN_magnetic_field_reading_set_WHEN_read_THEN_magnetic_field_reading_is_as_expected(self):
        expected_field_reading = 400
        self._set_magnetic_field_reading(expected_field_reading)
        self.ca.assert_that_pv_is("LKSH460_01:FIELDREADING", expected_field_reading)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_magnetic_field_reading_unit_set_WHEN_read_THEN_magnetic_field_reading_unit_is_as_expected(self):
        inputs = [0, 1, 2, 3]
        expected_unit = ["uG", "mG", "G", "kG"]
        for input, output in zip(inputs, expected_unit):
            self.ca.set_pv_value("LKSH460_01:FIELD:MULTIPLIER", input)
            self.ca.assert_that_pv_is("LKSH460_01:FIELDREADING.EGU", output)



