import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

import math


class FermichopperTests(unittest.TestCase):
    """
    Tests for the Fermi Chopper IOC.
    """

    valid_commands = ["0001", "0002", "0003","0004", "0005"]
    test_chopper_speeds = [150, 350, 600]
    test_delay_durations = [0, 2.5, 18]
    test_gatewidth_values = [0, 0.5, 5]
    test_temperature_values = [20.0, 25.0, 37.5, 47.5]
    test_current_values = [0, 1.37, 2.22]
    test_voltage_values = [0, 282.9, 333.3]
    test_autozero_values = [-5.0, -2.22, 0, 1.23, 5]

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("fermichopper")

        self.ca = ChannelAccess(15)
        self.ca.wait_for("FERMCHOP_01:DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("FERMCHOP_01:DISABLE", "COMMS ENABLED")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_last_command_is_set_via_backdoor_THEN_pv_updates(self):
        for value in self.valid_commands:
            self._lewis.backdoor_command(["device", "last_command", "'" + value + "'"])
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", value)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_last_command_is_set_THEN_readback_updates(self):
        for value in self.valid_commands:
            self.ca.set_pv_value("FERMCHOP_01:COMMAND:SP", value)
            self.ca.assert_that_pv_is("FERMCHOP_01:LASTCOMMAND", value)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_speed_setpoint_is_set_via_backdoor_THEN_pv_updates(self):
        for value in self.test_chopper_speeds:
            self._lewis.backdoor_command(["device", "speed_setpoint", str(value)])
            self.ca.assert_that_pv_is("FERMCHOP_01:SPEED:SP:RBV", value)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
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
            self._lewis.backdoor_command(["device", "delay", str(value)])
            self.ca.assert_that_pv_is_number("FERMCHOP_01:DELAY:SP:RBV", value, tolerance=0.05)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
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
            self._lewis.backdoor_command(["device", "gatewidth", str(value)])
            self.ca.assert_that_pv_is_number("FERMCHOP_01:GATEWIDTH", value, tolerance=0.05)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_gatewidth_is_set_THEN_readback_updates(self):
        for value in self.test_gatewidth_values:
            self.ca.set_pv_value("FERMCHOP_01:GATEWIDTH:SP", value)
            self.ca.assert_that_pv_is("FERMCHOP_01:GATEWIDTH:SP", value)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:GATEWIDTH:SP", self.ca.ALARM_NONE)
            self.ca.assert_that_pv_is_number("FERMCHOP_01:GATEWIDTH", value, tolerance=0.05)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:GATEWIDTH", self.ca.ALARM_NONE)

    def test_WHEN_autozero_voltages_are_set_via_backdoor_THEN_pvs_update(self):
        for number in ["1", "2"]:
            for boundary in ["upper", "lower"]:
                for value in self.test_autozero_values:
                    self._lewis.backdoor_command(["device", "autozero_{n}_{b}".format(n=number, b=boundary), str(value)])
                    self.ca.assert_that_pv_is_number("FERMCHOP_01:AUTOZERO:{n}:{b}".format(n=number, b=boundary.upper()), value, tolerance=0.05)
                    self.ca.assert_pv_alarm_is("FERMCHOP_01:AUTOZERO:{n}:{b}".format(n=number, b=boundary.upper()), self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_drive_voltage_is_set_via_backdoor_THEN_pv_updates(self):
        for voltage in self.test_voltage_values:
            self._lewis.backdoor_command(["device", "voltage", str(voltage)])
            self.ca.assert_that_pv_is_number("FERMCHOP_01:VOLTAGE", voltage, tolerance=0.1)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:VOLTAGE", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_drive_current_is_set_via_backdoor_THEN_pv_updates(self):
        for current in self.test_current_values:
            self._lewis.backdoor_command(["device", "current", str(current)])
            self.ca.assert_that_pv_is_number("FERMCHOP_01:CURRENT", current, tolerance=0.1)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:CURRENT", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_the_electronics_temperature_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in self.test_temperature_values:
            self._lewis.backdoor_command(["device", "electronics_temp", str(temp)])
            self.ca.assert_that_pv_is_number("FERMCHOP_01:TEMPERATURE:ELECTRONICS", temp, tolerance=0.2)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:TEMPERATURE:ELECTRONICS", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_WHEN_the_motor_temperature_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in self.test_temperature_values:
            self._lewis.backdoor_command(["device", "motor_temp", str(temp)])
            self.ca.assert_that_pv_is_number("FERMCHOP_01:TEMPERATURE:MOTOR", temp, tolerance=0.2)
            self.ca.assert_pv_alarm_is("FERMCHOP_01:TEMPERATURE:MOTOR", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_get_status(self):
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B0", "1")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B1", "1")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B2", "1")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B3", "1")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B4", "1")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B5", "1")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B6", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B7", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B8", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.B9", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BA", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BB", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BC", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BD", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BE", "0")
        self.ca.assert_that_pv_is("FERMCHOP_01:STATUS.BF", "0")
        self.ca.assert_pv_alarm_is("FERMCHOP_01:STATUS", self.ca.ALARM_NONE)
