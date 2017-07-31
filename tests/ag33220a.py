import unittest

from utils.channel_access import ChannelAccess


class Ag33220aTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess()
        self.ca.wait_for("AG33220A_01:DISABLE", timeout=30)

    def reset_values(self):
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 0.1)
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 1000)
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 0)
        self.ca.set_pv_value("AG33220A_01:FUNCTION:SP", 0)

    def test_GIVEN_amplitude_change_WHEN_read_THEN_amplitude_is_as_expected(self):
        self.reset_values()
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 0.1)
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 5)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE:SP:RBV", 5)

    def test_GIVEN_a_change_in_output_WHEN_read_THEN_the_expected_string_is_returned(self):
        self.ca.set_pv_value("AG33220A_01:OUTPUT:SP", "1")
        self.ca.assert_that_pv_is("AG33220A_01:OUTPUT", "ON")
        self.ca.set_pv_value("AG33220A_01:OUTPUT:SP", 0)  # Issue with ca when setting to "OFF"
        self.ca.assert_that_pv_is("AG33220A_01:OUTPUT:SP:RBV", "OFF")

    def test_GIVEN_a_change_in_function_over_the_maximum_WHEN_set_THEN_an_expected_limited_value_is_returned(self):
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 1*10**8)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 2*10**7)
        self.ca.set_pv_value("AG33220A_01:FUNCTION:SP", 2)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 2*10**5)

    def test_GIVEN_volt_high_is_set_lower_than_volt_low_WHEN_set_THEN_volt_low_is_set_lower_than_volt_high_by_the_expected_amount(self):
        first_volt_low = self.ca.get_pv_value("AG33220A_01:VOLT:LOW:SP:RBV") # self.ca.get_pv_value
        self.ca.set_pv_value("AG33220A_01:VOLT:HIGH:SP", first_volt_low)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", first_volt_low)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", first_volt_low-0.01)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 0.01)
        self.ca.assert_that_pv_is("AG33220A_01:OFFSET", first_volt_low-0.005)

    def test_GIVEN_change_in_volt_low_to_below_range_WHEN_set_THEN_value_is_limited(self):
        self.ca.set_pv_value("AG33220A_01:VOLT:LOW:SP", -10)
        self.ca.set_pv_value("AG33220A_01:VOLT:HIGH:SP", 0)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", -5)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 5)
        self.ca.assert_that_pv_is("AG33220A_01:OFFSET", -2.5)

    def test_GIVEN_idn_request_WHEN_read_THEN_expected_idn_is_returned(self):
        self.ca.assert_that_pv_is("AG33220A_01:IDN", "Agilent Technologies,33220A")

    def test_GIVEN_offset_set_to_2_and_half_and_amplitude_to_5_WHEN_read_THEN_volt_high_and_volt_low_are_as_expected(self):
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 2.5)
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 5)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", 5)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", 0)

    def test_GIVEN_offset_and_amplitude_are_reset_WHEN_set_THEN_volt_low_and_high_are_as_expected(self):
        self.ca.set_pv_value("AG33220A_01:VOLT:HIGH:SP", 5)
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 2.5)
        self.ca.set_pv_value("AG33220A_01:OFFSET:SP", 0)
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 2)
        self.ca.assert_that_pv_is("AG33220A_01:OFFSET", 0)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", 1)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", -1)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE", 2)

    def test_GIVEN_a_change_in_units_WHEN_read_THEN_the_appropriate_string_is_returned(self):
        self.ca.set_pv_value("AG33220A_01:UNITS:SP", 1)
        self.ca.assert_that_pv_is("AG33220A_01:UNITS", "VRMS")

    def test_GIVEN_max_frequency_and_change_in_function_WHEN_set_THEN_frequency_is_limited_as_expected(self):
        self.reset_values()
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 10**10)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 2*10**7)
        self.ca.set_pv_value("AG33220A_01:FUNCTION:SP", 2)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 2*10**5)

    def test_GIVEN_amplitude_less_than_min_WHEN_set_THEN_amplitude_is_limited(self):
        self.reset_values()
        self.ca.set_pv_value("AG33220A_01:AMPLITUDE:SP", 0)
        self.ca.assert_that_pv_is("AG33220A_01:AMPLITUDE:SP:RBV", 0.01)

    def test_GIVEN_voltage_low_is_set_higher_than_voltage_high_max_WHEN_set_THEN_voltage_low_and_high_are_as_expected(self):
        self.reset_values()
        self.ca.set_pv_value("AG33220A_01:VOLT:LOW:SP", 10)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:HIGH", 5)
        self.ca.assert_that_pv_is("AG33220A_01:VOLT:LOW", 4.99)

    def test_GIVEN_min_frequency_and_change_in_function_WHEN_set_THEN_frequency_is_kept_as_expected(self):
        self.reset_values()
        self.ca.set_pv_value("AG33220A_01:FUNCTION:SP", 3)
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 0)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 5*10**-4)
        self.ca.set_pv_value("AG33220A_01:FUNCTION:SP", 6)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 5*10**-4)
        self.ca.set_pv_value("AG33220A_01:FREQUENCY:SP", 0)
        self.ca.assert_that_pv_is("AG33220A_01:FREQUENCY", 10**-6)
