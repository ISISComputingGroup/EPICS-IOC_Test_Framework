import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc


class Instron_stress_rigTests(unittest.TestCase):
    """
    Tests for the Instron IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("instron_stress_rig")

        self.ca = ChannelAccess(15)
        self.ca.wait_for("INSTRON_01:CHANNEL", timeout=30)

    def test_that_when_the_rig_is_initialized_the_status_is_ok(self):
        self.ca.assert_that_pv_is("INSTRON_01:STAT:DISP", "System OK")

    def test_that_when_the_rig_is_initialized_it_is_not_going(self):
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")

    def test_that_when_the_rig_is_initialized_it_is_not_panic_stopping(self):
        self.ca.assert_that_pv_is("INSTRON_01:PANIC:SP", "READY")

    def test_that_when_the_rig_is_initialized_it_is_not_stopping(self):
        self.ca.assert_that_pv_is("INSTRON_01:STOP:SP", "READY")

    def test_that_the_rig_is_not_normally_in_control_mode(self):
        self.ca.assert_that_pv_is("INSTRON_01:STOP:SP", "READY")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_that_going_and_then_stopping_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")
        self.ca.set_pv_value("INSTRON_01:MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "YES")
        self.ca.set_pv_value("INSTRON_01:STOP:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_that_going_and_then_panic_stopping_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")
        self.ca.set_pv_value("INSTRON_01:MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "YES")
        self.ca.set_pv_value("INSTRON_01:PANIC:SP", 1)
        self.ca.assert_that_pv_is("INSTRON_01:GOING", "NO")

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_that_an_arbitrary_command_Q22_can_be_sent(self):
        self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "Q22")
        # Assert that the response to Q22 is a status code
        self.ca.assert_that_pv_is_an_integer_between("INSTRON_01:ARBITRARY", min=0, max=65535)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_that_an_arbitrary_command_Q300_can_be_sent(self):
        self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "Q300")
        # Assert that the response to Q300 is between 1 and 3
        self.ca.assert_that_pv_is_an_integer_between("INSTRON_01:ARBITRARY", min=1, max=3)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_that_an_arbitrary_command_C1_and_Q1_act_as_expected(self):

        def _set_and_check(value):
            self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "C1," + value)
            self.ca.assert_that_pv_is("INSTRON_01:ARBITRARY:SP", "C1," + value)
            self.ca.set_pv_value("INSTRON_01:ARBITRARY:SP", "Q1")
            self.ca.assert_that_pv_is("INSTRON_01:ARBITRARY", value)

        for v in ["0", "1", "0"]:
            _set_and_check(v)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_that_if_the_movement_type_on_rig_is_hold_then_it_gets_stopped(self):

        self.ca.set_pv_value("INSTRON_01:MOVE:SP", 1)
        self.ca.assert_that_pv_is_one_of("INSTRON_01:MOVE", ["RAMP_RUNNING", "RAND_RUNNING"])

        self.ca.set_pv_value("INSTRON_01:MOVE:SP", 2)
        self.ca.assert_that_pv_is("INSTRON_01:MOVE", "STOPPED")

    def test_that_control_channel_is_one_of_the_allowed_values(self):
        self.ca.assert_that_pv_is_one_of("INSTRON_01:CHANNEL", ["Stress", "Strain", "Position"])

    def test_that_control_channel_setpoint_is_one_of_the_allowed_values(self):
        self.ca.assert_that_pv_is_one_of("INSTRON_01:CHANNEL:SP", ["Stress", "Strain", "Position"])

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_that_setting_the_control_channel_works_as_expected(self):

        def _set_and_check(set_value, return_value):
            self.ca.set_pv_value("INSTRON_01:CHANNEL:SP", set_value)
            self.ca.assert_that_pv_is("INSTRON_01:CHANNEL", return_value)

        for set_val, return_val in [(0, "Position"), (1, "Stress"), (2, "Strain")]:
            _set_and_check(set_val, return_val)

