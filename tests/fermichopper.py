import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

from time import sleep


class FermichopperTests(unittest.TestCase):
    """
    Tests for the Fermi Chopper IOC.
    """

    valid_commands = ["0001", "0002", "0003","0004", "0005"]

    # Values that will be tested in the parametrized tests.
    test_chopper_speeds = [100, 350, 600]
    test_delay_durations = [0, 2.5, 18]
    test_gatewidth_values = [0, 0.5, 5]
    test_temperature_values = [20.0, 25.0, 37.5, 47.5]
    test_current_values = [0, 1.37, 2.22]
    test_voltage_values = [0, 282.9, 333.3]
    test_autozero_values = [-5.0, -2.22, 0, 1.23, 5]

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("fermichopper")

        self.ca = ChannelAccess(20)
        self.ca.wait_for("FERMCHOP_01:SPEED", timeout=30)

        if not IOCRegister.uses_rec_sim:

            # Ensure consistent startup state...
            self._lewis.backdoor_set_on_device("electronics_temp", 20)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:TEMPERATURE:ELECTRONICS", 20, tolerance=0.2)

            self._lewis.backdoor_set_on_device("motor_temp", 20)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:TEMPERATURE:MOTOR", 20, tolerance=0.2)

            for number in [1, 2]:
                for position in ["upper", "lower"]:
                    self._lewis.backdoor_set_on_device("autozero_{n}_{p}".format(n=number, p=position), 0)
                    self.ca.assert_that_pv_is_number(
                        "FERMCHOP_01:AUTOZERO:{n}:{p}".format(n=number, p=position.upper()), 0, tolerance=0.1)

            self._lewis.backdoor_set_on_device("speed", 0)

            self._lewis.backdoor_set_on_device("do_command", "0001")
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0001")

            self._lewis.backdoor_set_on_device("speed_setpoint", 0)
            self.ca.assert_that_pv_is("FERMCHOP_01:SPEED:SP:RBV", 0)

            self._lewis.backdoor_set_on_device("magneticbearing", False)
            self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "0")

            self._lewis.backdoor_set_on_device("speed", 0)
            self.ca.assert_that_pv_is("FERMCHOP_01:SPEED", 0)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("FERMCHOP_01:DISABLE", "COMMS ENABLED")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_last_command_is_set_via_backdoor_THEN_pv_updates(self):
        for value in self.valid_commands:
            # Doesn't actually execute the commands, so we are safe from entering the "broken" state here.
            self._lewis.backdoor_set_on_device("last_command", value)
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", value)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_speed_setpoint_is_set_via_backdoor_THEN_pv_updates(self):
        for value in self.test_chopper_speeds:
            self._lewis.backdoor_set_on_device("speed_setpoint", value)
            self.ca.assert_that_pv_is("FERMCHOP_01:SPEED:SP:RBV", value)

    # @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_speed_setpoint_is_set_THEN_readback_updates(self):
        for speed in self.test_chopper_speeds:
            self.ca.set_pv_value("FERMCHOP_01:SPEED:SP", speed)
            self.ca.assert_that_pv_is("FERMCHOP_01:SPEED:SP", speed)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:SPEED:SP", self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is("FERMCHOP_01:SPEED:SP:RBV", speed)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:SPEED:SP:RBV", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_delay_setpoint_is_set_via_backdoor_THEN_pv_updates(self):
        for value in self.test_delay_durations:
            self._lewis.backdoor_set_on_device("delay", value)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:DELAY:SP:RBV", value, tolerance=0.05)

    # @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_delay_setpoint_is_set_THEN_readback_updates(self):
        for value in self.test_delay_durations:
            self.ca.set_pv_value("FERMCHOP_01:DELAY:SP", value)
            self.ca.assert_that_pv_is("FERMCHOP_01:DELAY:SP", value)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:DELAY:SP", self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:DELAY:SP:RBV", value, tolerance=0.05)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:DELAY:SP:RBV", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_gatewidth_setpoint_is_set_via_backdoor_THEN_pv_updates(self):
        for value in self.test_gatewidth_values:
            self._lewis.backdoor_set_on_device("gatewidth", value)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:GATEWIDTH", value, tolerance=0.05)

    # @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_gatewidth_is_set_THEN_readback_updates(self):
        for value in self.test_gatewidth_values:
            self.ca.set_pv_value("FERMCHOP_01:GATEWIDTH:SP", value)
            self.ca.assert_that_pv_is("FERMCHOP_01:GATEWIDTH:SP", value)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:GATEWIDTH:SP", self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:GATEWIDTH", value, tolerance=0.05)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:GATEWIDTH", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_autozero_voltages_are_set_via_backdoor_THEN_pvs_update(self):
        for number in ["1", "2"]:
            for boundary in ["upper", "lower"]:
                for value in self.test_autozero_values:
                    self._lewis.backdoor_set_on_device("autozero_{n}_{b}".format(n=number, b=boundary), value)
                    self.ca.assert_that_pv_is_number("FERMCHOP_01:AUTOZERO:{n}:{b}".format(n=number, b=boundary.upper()), value, tolerance=0.05)
                    self.ca.assert_pv_alarm_is("FERMCHOP_01:AUTOZERO:{n}:{b}".format(n=number, b=boundary.upper()), self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_drive_voltage_is_set_via_backdoor_THEN_pv_updates(self):
        for voltage in self.test_voltage_values:
            self._lewis.backdoor_set_on_device("voltage", voltage)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:VOLTAGE", voltage, tolerance=0.1)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:VOLTAGE", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_drive_current_is_set_via_backdoor_THEN_pv_updates(self):
        for current in self.test_current_values:
            self._lewis.backdoor_set_on_device("current", current)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:CURRENT", current, tolerance=0.1)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:CURRENT", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_the_electronics_temperature_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in self.test_temperature_values:
            self._lewis.backdoor_set_on_device("electronics_temp", temp)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:TEMPERATURE:ELECTRONICS", temp, tolerance=0.2)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:TEMPERATURE:ELECTRONICS", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_the_motor_temperature_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in self.test_temperature_values:
            self._lewis.backdoor_set_on_device("motor_temp", temp)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:TEMPERATURE:MOTOR", temp, tolerance=0.2)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:TEMPERATURE:MOTOR", self.ca.ALARM_NONE)


    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_a_stopped_chopper_WHEN_start_command_is_sent_THEN_chopper_goes_to_setpoint(self):
        for speed in self.test_chopper_speeds:
            # Setup setpoint speed
            self._lewis.backdoor_set_on_device("speed_setpoint", speed)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:SPEED:SP:RBV", speed)

            # Switch on magnetic bearings
            self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 4)
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0004")
            self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "1")

            # Run mode ON
            self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 3)
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0003")

            self.ca.assert_that_pv_is_number("FERMCHOP_01:SPEED", speed, tolerance=0.1, timeout=30)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_a_stopped_chopper_WHEN_start_command_is_sent_without_magnetic_bearings_on_THEN_chopper_does_not_go_to_setpoint(self):

        # Switch OFF magnetic bearings
        self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 5)
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0005")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "0")

        for speed in self.test_chopper_speeds:
            # Setup setpoint speed
            self._lewis.backdoor_set_on_device("speed_setpoint", speed)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:SPEED:SP:RBV", speed)

            # Run mode ON
            self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 3)
            # Ensure the ON command has been ignored and last command is still "switch off bearings"
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0005")

            self.ca.assert_that_pv_is_number("FERMCHOP_01:SPEED", 0, tolerance=0.1, timeout=30)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_a_chopper_at_speed_WHEN_switch_off_magnetic_bearings_command_is_sent_THEN_magnetic_bearings_do_not_switch_off(self):

        speed = 150

        # Switch ON magnetic bearings
        self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 4)
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0004")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "1")

        # Setup setpoint speed
        self._lewis.backdoor_set_on_device("speed_setpoint", speed)
        self.ca.assert_that_pv_is_number("FERMCHOP_01:SPEED:SP:RBV", speed)

        # Run mode ON
        self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 3)
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0003")

        # Wait for chopper to get up to speed
        self.ca.assert_that_pv_is_number("FERMCHOP_01:SPEED", speed, tolerance=0.1)

        # Attempt to switch OFF magnetic bearings
        self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 5)

        # Assert that bearings did not switch off
        sleep(5)
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0003")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "1")
        self.ca.assert_that_pv_is("FERMCHOP_01:SPEED", speed)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_a_stopped_chopper_WHEN_switch_on_and_off_magnetic_bearings_commands_are_sent_THEN_magnetic_bearings_switch_on_and_off(self):

        # Switch ON magnetic bearings
        self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 4)
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0004")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "1")

        # Switch OFF magnetic bearings
        self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", 5)
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0005")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "0")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_chopper_speed_is_too_high_THEN_status_updates(self):

        too_fast = 700

        self._lewis.backdoor_set_on_device("speed", too_fast)
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BA", "1")

        self._lewis.backdoor_set_on_device("speed", 0)
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BA", "0")


    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_chopper_speed_is_too_high_with_magnetic_bearing_off_THEN_status_updates(self):

        too_fast = 15

        # Magnetic bearings should have been turned off in setUp
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "0")

        self._lewis.backdoor_set_on_device("speed", too_fast)
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BB", "1")

        self._lewis.backdoor_set_on_device("magneticbearing", True)
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BB", "0")

        self._lewis.backdoor_set_on_device("magneticbearing", False)
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BB", "1")

        self._lewis.backdoor_set_on_device("speed", 0)
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BB", "0")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_chopper_parameters_are_set_THEN_status_updates(self):

        for command_number, b6, b8, b9 in [(6, 1, 0, 0), (7, 0, 1, 0), (8, 0, 0, 1)]:

            # Magnetic bearings should have been turned off in setUp
            self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "0")

            self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", command_number)
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "000{}".format(command_number))

            self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B6", "{}".format(b6))
            self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B8", "{}".format(b8))
            self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B9", "{}".format(b9))


    #
    #   Mandatory safety tests
    #
    #   The following behaviours MUST be implemented by the chopper according to the manual
    #

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_chopper_speed_is_too_high_THEN_switch_drive_off_is_sent(self):
        self._lewis.backdoor_set_on_device("magneticbearing", True)
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "1")

        # Reset last command so that we can tell that it's changed later on
        self._lewis.backdoor_set_on_device("last_command", "0000")
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0000")

        # Speed = 610, this is higher than the maximum allowed speed (606)
        self._lewis.backdoor_set_on_device("speed", 610)

        # Assert that "switch drive off" was sent
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0002")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_magnetic_bearing_is_off_WHEN_chopper_speed_is_moving_THEN_switch_drive_on_and_stop_is_sent(self):

        # Magnetic bearings should have been turned off in setUp
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "0")

        # Reset last command so that we can tell that it's changed later on
        self._lewis.backdoor_set_on_device("last_command", "0000")
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0000")

        # Speed = 7 because that's higher than the threshold in the IOC (5)
        # but lower than the threshold in the emulator (10)
        self._lewis.backdoor_set_on_device("speed", 7)

        # Assert that "switch drive on and stop" was sent
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0001")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_GIVEN_autozero_voltages_are_out_of_range_WHEN_chopper_is_moving_THEN_switch_drive_on_and_stop_is_sent(self):

        for number in [1, 2]:
            for position in ["upper", "lower"]:

                # Reset last command so that we can tell that it's changed later on
                self._lewis.backdoor_set_on_device("last_command", "0000")
                self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0000")

                # Set autozero voltage too high and set device moving
                self._lewis.backdoor_set_on_device("autozero_{n}_{p}".format(n=number, p=position), 3.2)
                self._lewis.backdoor_set_on_device("speed", 7)

                # Assert that "switch drive on and stop" was sent
                self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0001")

                # Reset relevant autozero voltage back to zero
                self._lewis.backdoor_set_on_device("autozero_{n}_{p}".format(n=number, p=position), 0)
                self.ca.assert_that_pv_is_number("FERMCHOP_01:AUTOZERO:{n}:{p}".format(n=number, p=position.upper()), 0, tolerance=0.1)

                # Give the IOC time to accept that it is now in a valid state again...
                sleep(3)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_motor_temperature_is_too_high_THEN_switch_drive_off_is_sent(self):

        # Reset last command so that we can tell that it's changed later on
        self._lewis.backdoor_set_on_device("last_command", "0000")
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0000")

        # Temperature = 46, this is higher than the allowed value (45)
        self._lewis.backdoor_set_on_device("motor_temp", 46)

        # Assert that "switch drive off" was sent
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0002")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_electronics_temperature_is_too_high_THEN_switch_drive_off_is_sent(self):
        # Reset last command so that we can tell that it's changed later on
        self._lewis.backdoor_set_on_device("last_command", "0000")
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0000")

        # Temperature = 46, this is higher than the allowed value (45)
        self._lewis.backdoor_set_on_device("electronics_temp", 46)

        # Assert that "switch drive off" was sent
        self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", "0002")
