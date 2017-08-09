import unittest
from unittest import skipIf

from utils.ioc_launcher import IOCRegister
from utils.channel_access import ChannelAccess


class Ag33220aTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess()
        self.ca.wait_for("AG33220A_01:DISABLE", timeout=30)
        self.reset_values()

    def reset_values(self):
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 0.1)
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 1000)
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 0)
        self.ca.set_pv_value("AG33220A_01:FUNCTION:SP", 0)

    def test_WHEN_amplitude_change_to_5_THEN_readback_is_5(self):
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 5)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 5)

    def test_WHEN_units_changed_to_1_THEN_vrms_is_returned(self):
        self.ca.set_pv_value("AG33220A_01:UNITS:SP", 1)
        self.ca.assert_that_pv_is("AG33220A_01:UNITS", "VRMS")

    def test_WHEN_output_changed_THEN_the_expected_output_string_is_read_back(self):
        self.ca.set_pv_value("AG33220A_01:OUTPUT:SP", 1)
        self.ca.assert_that_pv_is("AG33220A_01:OUTPUT", "ON")
        self.ca.set_pv_value("AG33220A_01:OUTPUT:SP", 0)
        self.ca.assert_that_pv_is("AG33220A_01:OUTPUT", "OFF")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_frequency_is_set_higher_than_allowed_THEN_it_is_limited(self):
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 1*10**8)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 2*10**7)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_a_change_in_function_over_the_maximum_THEN_the_frequency_is_changed(self):
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 1e8)
        self.ca.set_pv_value("AG33220A_01:FUNCTION:SP", 2)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 2*10**5)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_volt_high_is_set_lower_than_volt_low_THEN_volt_low_is_reduced(self):
        self.ca.set_pv_value("AG33220A_01:VOLT:HIGH:SP", 1)
        self.ca.set_pv_value("AG33220A_01:VOLT:LOW:SP", -1)
        self.ca.set_pv_value("AG33220A_01:VOLT:HIGH:SP", -2)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", -2)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", -2.01)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 0.01)
        self.ca.assert_that_pv_is("AG33220A_01:OFFSET", -2.005)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_change_in_volt_low_to_below_range_THEN_value_is_limited(self):
        self.ca.set_pv_value("AG33220A_01:VOLT:LOW:SP", -10)
        self.ca.set_pv_value("AG33220A_01:VOLT:HIGH:SP", 0)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", -5)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 5)
        self.ca.assert_that_pv_is("AG33220A_01:OFFSET", -2.5)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_idn_request_WHEN_read_THEN_expected_idn_is_returned(self):
        self.ca.assert_that_pv_is("AG33220A_01:IDN", "Agilent Technologies,33220A")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_offset_set_to_2_and_half_and_amplitude_to_5_THEN_volt_high_is_5_and_volt_low_is_0(self):
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 2.5)
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 5)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", 5)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", 0)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_offset_set_to_0_and_2_THEN_volt_low_is_neg_1_and_high_is_1(self):
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 0)
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 2)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", 1)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", -1)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_amplitude_set_to_less_than_min_THEN_amplitude_is_limited(self):
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 0)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 0.01)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_offset_changed_to_cause_voltage_larger_than_max_THEN_amplitude_reduced(self):
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 0)
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 6)

        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 3)

        self.ca.assert_that_pv_is("AG33220A_01:OFFSET", 3)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 4)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", 1)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", 5)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_amplitude_changed_to_cause_voltage_larger_than_max_THEN_offset_reduced(self):
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 3)
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 2)

        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 6)

        self.ca.assert_that_pv_is("AG33220A_01:OFFSET", 2)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 6)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", -1)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", 5)
        
