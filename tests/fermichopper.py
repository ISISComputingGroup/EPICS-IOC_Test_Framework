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

    valid_commands = ["0001", "0002", "0003", "0006", "0007"]

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
    def test_get_speed_sp_rbv_returns_18000(self):
        self.ca.assert_that_pv_is("FERMCHOP_01:SPEED:SP:RBV", 18000)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:SPEED:SP:RBV", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_get_speed_returns_17999(self):
        self.ca.assert_that_pv_is("FERMCHOP_01:SPEED", 17999)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:SPEED", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_get_delay_sp_rbv_returns_416_and_two_thirds(self):
        self.ca.assert_that_pv_is_number("FERMCHOP_01:DELAY:SP:RBV", 416.67, tolerance=0.02)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:DELAY:SP:RBV", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_get_delay_returns_416_and_two_thirds(self):
        self.ca.assert_that_pv_is_number("FERMCHOP_01:DELAY", 416.67, tolerance=0.02)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:DELAY", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_get_gatewidth_returns_833_nsec(self):
        self.ca.assert_that_pv_is_number("FERMCHOP_01:GATEWIDTH", 0.833, tolerance=0.001)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:GATEWIDTH", self.ca.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_get_drive_current(self):
        self.ca.assert_that_pv_is_number("FERMCHOP_01:DRIVECURRENT", 0.98985, tolerance=0.00005)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:DRIVECURRENT", self.ca.ALARM_NONE)

    def test_get_autozero_voltages(self):
        self.ca.assert_that_pv_is_number("FERMCHOP_01:AUTOZERO:1:UPPER", -0.6, tolerance=0.05)
        self.ca.assert_that_pv_is_number("FERMCHOP_01:AUTOZERO:2:UPPER", -0.2, tolerance=0.05)
        self.ca.assert_that_pv_is_number("FERMCHOP_01:AUTOZERO:1:LOWER", -0.1, tolerance=0.05)
        self.ca.assert_that_pv_is_number("FERMCHOP_01:AUTOZERO:2:LOWER", 0.6, tolerance=0.05)

        self.ca.assert_pv_alarm_is("FERMCHOP_01:AUTOZERO:1:UPPER", self.ca.ALARM_NONE)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:AUTOZERO:2:UPPER", self.ca.ALARM_NONE)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:AUTOZERO:1:LOWER", self.ca.ALARM_NONE)
        self.ca.assert_pv_alarm_is("FERMCHOP_01:AUTOZERO:1:LOWER", self.ca.ALARM_NONE)
