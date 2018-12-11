import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import skip_if_recsim, get_running_lewis_and_ioc


DEVICE_PREFIX = "AG33220A_01"
emulator_name = "ag33220a"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("AG33220A"),
        "macros": {},
        "emulator": emulator_name,
        "emulator_protocol": "stream",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class Ag33220aTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(emulator_name, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self.ca.assert_that_pv_exists("DISABLE", timeout=30)
        self.reset_values()

    def reset_values(self):
        self.ca.set_pv_value("AMPLITUDE:SP", 0.1)
        self.ca.set_pv_value("FREQUENCY:SP", 1000)
        self.ca.set_pv_value("OFFSET:SP", 0)
        self.ca.set_pv_value("FUNCTION:SP", 0)

    def test_WHEN_amplitude_change_to_5_THEN_readback_is_5(self):
        self.ca.set_pv_value("AMPLITUDE:SP", 5)
        self.ca.assert_that_pv_is("AMPLITUDE", 5)

    def test_WHEN_units_changed_to_1_THEN_vrms_is_returned(self):
        self.ca.set_pv_value("UNITS:SP", 1)
        self.ca.assert_that_pv_is("UNITS", "VRMS")

    def test_WHEN_output_changed_THEN_the_expected_output_string_is_read_back(self):
        self.ca.set_pv_value("OUTPUT:SP", 1)
        self.ca.assert_that_pv_is("OUTPUT", "ON")
        self.ca.set_pv_value("OUTPUT:SP", 0)
        self.ca.assert_that_pv_is("OUTPUT", "OFF")

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_frequency_is_set_higher_than_allowed_THEN_it_is_limited(self):
        self.ca.set_pv_value("FREQUENCY:SP", 1*10**8)
        self.ca.assert_that_pv_is("FREQUENCY", 2*10**7)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_a_change_in_function_over_the_maximum_THEN_the_frequency_is_changed(self):
        self.ca.set_pv_value("FREQUENCY:SP", 1e8)
        self.ca.set_pv_value("FUNCTION:SP", 2)
        self.ca.assert_that_pv_is("FREQUENCY", 2*10**5)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_volt_high_is_set_lower_than_volt_low_THEN_volt_low_is_reduced(self):
        self.ca.set_pv_value("VOLT:HIGH:SP", 1)
        self.ca.set_pv_value("VOLT:LOW:SP", -1)
        self.ca.set_pv_value("VOLT:HIGH:SP", -2)
        self.ca.assert_that_pv_is("VOLT:HIGH", -2)
        self.ca.assert_that_pv_is("VOLT:LOW", -2.01)
        self.ca.assert_that_pv_is("AMPLITUDE", 0.01)
        self.ca.assert_that_pv_is("OFFSET", -2.005)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_change_in_volt_low_to_below_range_THEN_value_is_limited(self):
        self.ca.set_pv_value("VOLT:LOW:SP", -10)
        self.ca.set_pv_value("VOLT:HIGH:SP", 0)
        self.ca.assert_that_pv_is("VOLT:LOW", -5)
        self.ca.assert_that_pv_is("AMPLITUDE", 5)
        self.ca.assert_that_pv_is("OFFSET", -2.5)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_idn_request_WHEN_read_THEN_expected_idn_is_returned(self):
        self.ca.assert_that_pv_is("IDN", "Agilent Technologies,33220A")

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_offset_set_to_2_and_half_and_amplitude_to_5_THEN_volt_high_is_5_and_volt_low_is_0(self):
        self.ca.set_pv_value("OFFSET:SP", 2.5)
        self.ca.set_pv_value("AMPLITUDE:SP", 5)
        self.ca.assert_that_pv_is("VOLT:HIGH", 5)
        self.ca.assert_that_pv_is("VOLT:LOW", 0)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_offset_set_to_0_and_2_THEN_volt_low_is_neg_1_and_high_is_1(self):
        self.ca.set_pv_value("OFFSET:SP", 0)
        self.ca.set_pv_value("AMPLITUDE:SP", 2)
        self.ca.assert_that_pv_is("VOLT:HIGH", 1)
        self.ca.assert_that_pv_is("VOLT:LOW", -1)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_amplitude_set_to_less_than_min_THEN_amplitude_is_limited(self):
        self.ca.set_pv_value("AMPLITUDE:SP", 0)
        self.ca.assert_that_pv_is("AMPLITUDE", 0.01)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_offset_changed_to_cause_voltage_larger_than_max_THEN_amplitude_reduced(self):
        self.ca.set_pv_value("OFFSET:SP", 0)
        self.ca.set_pv_value("AMPLITUDE:SP", 6)

        self.ca.set_pv_value("OFFSET:SP", 3)

        self.ca.assert_that_pv_is("OFFSET", 3)
        self.ca.assert_that_pv_is("AMPLITUDE", 4)
        self.ca.assert_that_pv_is("VOLT:LOW", 1)
        self.ca.assert_that_pv_is("VOLT:HIGH", 5)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_amplitude_changed_to_cause_voltage_larger_than_max_THEN_offset_reduced(self):
        self.ca.set_pv_value("OFFSET:SP", 3)
        self.ca.set_pv_value("AMPLITUDE:SP", 2)

        self.ca.set_pv_value("AMPLITUDE:SP", 6)

        self.ca.assert_that_pv_is("OFFSET", 2)
        self.ca.assert_that_pv_is("AMPLITUDE", 6)
        self.ca.assert_that_pv_is("VOLT:LOW", -1)
        self.ca.assert_that_pv_is("VOLT:HIGH", 5)

    @skip_if_recsim("Can not test disconnection in rec sim")
    def test_GIVEN_device_not_connected_WHEN_get_status_THEN_alarm(self):
        self._lewis.backdoor_set_on_device('connected', False)
        self.ca.assert_that_pv_alarm_is('FREQUENCY', ChannelAccess.Alarms.INVALID)
