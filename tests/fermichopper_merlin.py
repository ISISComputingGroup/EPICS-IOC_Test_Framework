import unittest
from utils.test_modes import TestModes
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import skip_if_recsim, assert_log_messages
from common_tests.fermichopper import FermichopperBase, ErrorStrings

DEVICE_PREFIX = "FERMCHOP_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("FERMCHOP"),
        "macros": {
            "INST": "merlin",
            "MHZ": "50.4",
        },
        "emulator": "fermichopper",
        "lewis_protocol": "fermi_merlin",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class MerlinFermiChopperTests(FermichopperBase, unittest.TestCase):
    """
    Most tests inherited from FermiChopperBase

    Tests in this class are for functionality that only exists on Merlin chopper not MAPS
    """

    def _get_device_prefix(self):
        return DEVICE_PREFIX

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_the_electronics_temperature_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in self.test_temperature_values:
            self._lewis.backdoor_set_on_device("electronics_temp", temp)
            self.ca.assert_that_pv_is_number("TEMP:ELECTRONICS", temp, tolerance=0.2)
            self.ca.assert_that_pv_alarm_is("TEMP:ELECTRONICS", self.ca.Alarms.NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_the_motor_temperature_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in self.test_temperature_values:
            self._lewis.backdoor_set_on_device("motor_temp", temp)
            self.ca.assert_that_pv_is_number("TEMP:MOTOR", temp, tolerance=0.2)
            self.ca.assert_that_pv_alarm_is("TEMP:MOTOR", self.ca.Alarms.NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_chopper_parameters_are_set_THEN_status_updates(self):

        for command_number, b6, b8, b9 in [(6, 1, 0, 0), (7, 0, 1, 0), (8, 0, 0, 1)]:

            # Magnetic bearings should have been turned off in setUp
            self.ca.assert_that_pv_is("STATUS.B3", "0")

            self.ca.set_pv_value("COMMAND:SP", command_number)
            self.ca.assert_that_pv_is("LASTCOMMAND", "000{}".format(command_number))

            self.ca.assert_that_pv_is("STATUS.B6", "{}".format(b6))
            self.ca.assert_that_pv_is("STATUS.B8", "{}".format(b8))
            self.ca.assert_that_pv_is("STATUS.B9", "{}".format(b9))

    @skip_if_recsim("Uses lewis backdoor")
    def test_WHEN_electronics_temperature_is_too_high_THEN_over_temperature_is_true(self):
        self.ca.assert_that_pv_is("TEMP:RANGECHECK", 0)
        with assert_log_messages(self._ioc, in_time=5, must_contain=ErrorStrings.ELECTRONICS_TEMP_TOO_HIGH):
            self._lewis.backdoor_set_on_device("electronics_temp", 46)
            self.ca.assert_that_pv_is("TEMP:RANGECHECK", 1)

    @skip_if_recsim("Uses lewis backdoor")
    def test_WHEN_motor_temperature_is_too_high_THEN_over_temperature_is_true(self):
        self.ca.assert_that_pv_is("TEMP:RANGECHECK", 0)
        with assert_log_messages(self._ioc, in_time=5, must_contain=ErrorStrings.MOTOR_TEMP_TOO_HIGH):
            self._lewis.backdoor_set_on_device("motor_temp", 46)
            self.ca.assert_that_pv_is("TEMP:RANGECHECK", 1)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_drive_voltage_is_set_via_backdoor_THEN_pv_updates(self):
        for voltage in self.test_voltage_values:
            self._lewis.backdoor_set_on_device("voltage", voltage)
            self.ca.assert_that_pv_is_number("VOLTAGE", voltage, tolerance=0.1)
            self.ca.assert_that_pv_alarm_is("VOLTAGE", self.ca.Alarms.NONE)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_motor_temperature_is_too_high_THEN_switch_drive_off_is_sent(self):

        # Reset last command so that we can tell that it's changed later on
        self._lewis.backdoor_set_on_device("last_command", "0000")
        self.ca.assert_that_pv_is("LASTCOMMAND", "0000")

        with assert_log_messages(self._ioc, in_time=5, must_contain=ErrorStrings.MOTOR_TEMP_TOO_HIGH):
            # Temperature = 46, this is higher than the allowed value (45)
            self._lewis.backdoor_set_on_device("motor_temp", 46)

            # Assert that "switch drive off" was sent
            self.ca.assert_that_pv_is("LASTCOMMAND", "0002")

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_electronics_temperature_is_too_high_THEN_switch_drive_off_is_sent(self):
        # Reset last command so that we can tell that it's changed later on
        self._lewis.backdoor_set_on_device("last_command", "0000")
        self.ca.assert_that_pv_is("LASTCOMMAND", "0000")

        with assert_log_messages(self._ioc, in_time=5, must_contain=ErrorStrings.ELECTRONICS_TEMP_TOO_HIGH):
            # Temperature = 46, this is higher than the allowed value (45)
            self._lewis.backdoor_set_on_device("electronics_temp", 46)

            # Assert that "switch drive off" was sent
            self.ca.assert_that_pv_is("LASTCOMMAND", "0002")

    @skip_if_recsim("Uses lewis backdoor")
    def test_WHEN_voltage_and_current_are_varied_THEN_power_pv_is_the_product_of_current_and_voltage(self):
        for voltage in self.test_voltage_values:
            for current in self.test_current_values:
                self._lewis.backdoor_set_on_device("voltage", voltage)
                self._lewis.backdoor_set_on_device("current", current)
                self.ca.assert_that_pv_is_number("POWER", current * voltage, tolerance=0.5)
