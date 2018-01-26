import unittest
from unittest import skipIf

from hamcrest import *

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

MACROS = {"MTRCTRL": "1",
          "AXIS1": "yes",
          "NAME1": "Sample Lin",
          "MSTP1": 200,
          "VELO1": 75,
          "DHLM1": 570,
          "DLLM1": -0.5,
          "AXIS2": "yes",
          "NAME2": "Sample Rot",
          "MSTP2": 1000,
          "VELO2": 15,
          "DHLM2": 640,
          "DLLM2": -0.2
          }


expected_reset_codes = [
    "PEK0", "PEL1",
    "B/ G01", "B/ G90",
    "PXA2", "PYA2",
    "PXB5", "PYB1",
    "PXC10", "PYC10",
    "PXD2500", "PYD2500",
    "PXE100000", "PYE25000",
    "PXF1000", "PYF1000",
    "PXG0", "PYG0",
    "PXH+57000", "PYH+64000",
    "PXI-50", "PYI-20",
    "PXJ2500", "PYJ25000",
    "PXK-2500", "PYK-7500",
    "PXL100", "PYL100",
    "PXM5", "PYM5",
    "PXN100", "PYN5000",
    "PXO0", "PYO0",
    "PXP0", "PYP0",
    "BF15000"
]

MTRPV = {
    "x": "MTR0101",
    "y": "MTR0101"
}

SM300_DEVICE_PREFIX = "SM300_01"


class Sm300Tests(unittest.TestCase):
    """
    Tests for the Samsm300 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("sm300")
        self.ca = ChannelAccess(device_prefix="MOT")
        self.ioc_ca = ChannelAccess(device_prefix=SM300_DEVICE_PREFIX)
        self.ioc_ca.wait_for("RESET_AND_HOME", timeout=30)
        self._lewis.backdoor_run_function_on_device("reset")

    def set_starting_position(self, starting_pos, axis="x"):
        """
        Set the starting position of the motor and check it is there.
        Args:
            starting_pos: position to start at in steps
            axis: axis to set position on

        """
        if IOCRegister.uses_rec_sim:
            resolution = self.ca.get_pv_value("{}.MRES".format(MTRPV[axis]))
            self.ca.set_pv_value(MTRPV[axis], starting_pos * resolution)
        self._lewis.backdoor_set_on_device(axis + "_axis_rbv", starting_pos)
        self._lewis.backdoor_set_on_device(axis + "_axis_sp", starting_pos)
        self.ca.assert_that_pv_is("{}.RRBV".format(MTRPV[axis]), starting_pos)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set x read back explicitly")
    def test_GIVEN_motor_at_position_WHEN_get_axis_x_ioc_position_THEN_position_is_as_expected(self):
        expected_value = 100
        resolution = self.ca.get_pv_value("MTR0101.MRES")
        self._lewis.backdoor_set_on_device("x_axis_rbv", expected_value / resolution)
        self._lewis.backdoor_set_on_device("x_axis_sp", expected_value / resolution)

        self.ca.assert_that_pv_is("MTR0101.RBV", expected_value)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set y read back explicitly")
    def test_GIVEN_motor_at_position_WHEN_get_axis_y_ioc_position_THEN_position_is_as_expected(self):
        expected_value = 95
        resolution = self.ca.get_pv_value("MTR0102.MRES")
        self._lewis.backdoor_set_on_device("y_axis_rbv", expected_value / resolution)
        self._lewis.backdoor_set_on_device("y_axis_sp", expected_value / resolution)

        self.ca.assert_that_pv_is("MTR0102.RBV", expected_value)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set error")
    def test_GIVEN_error_on_axis_WHEN_get_axis_x_THEN_error_returned(self):
        self._lewis.backdoor_set_on_device("x_axis_rbv_error", "B10")

        # It doesn't appear that the motor can be made to go into an invlaid state so major alarm will have to do
        self.ca.assert_pv_alarm_is("MTR0101", ChannelAccess.ALARM_INVALID)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set error")
    def test_GIVEN_malformed_motor_position_WHEN_get_axis_x_THEN_error_returned(self):
        self._lewis.backdoor_set_on_device("x_axis_rbv_error", "Xrubbish")

        # It doesn't appear that the motor can be made to go into an invlaid state so major alarm will have to do
        self.ca.assert_pv_alarm_is("MTR0101", ChannelAccess.ALARM_INVALID)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set moving on motor")
    def test_GIVEN_a_motor_is_moving_WHEN_get_moving_THEN_both_axis_are_moving(self):

        expected_value = 0
        self._lewis.backdoor_set_on_device("is_moving", True)

        self.ca.assert_that_pv_is("MTR0101.DMOV", expected_value)
        self.ca.assert_that_pv_is("MTR0102.DMOV", expected_value)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set moving on motor")
    def test_GIVEN_a_motor_is_not_moving_WHEN_get_moving_THEN_both_axis_are_not_moving(self):
        expected_value = 1
        self._lewis.backdoor_set_on_device("is_moving", False)

        self.ca.assert_that_pv_is("MTR0101.DMOV", expected_value)
        self.ca.assert_that_pv_is("MTR0102.DMOV", expected_value)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set moving error")
    def test_GIVEN_a_motor_is_in_error_WHEN_get_moving_THEN_both_axis_are_in_error(self):
        self._lewis.backdoor_set_on_device("is_moving_error", True)

        self.ca.assert_pv_alarm_is("MTR0101", ChannelAccess.ALARM_MAJOR)
        self.ca.assert_pv_alarm_is("MTR0102", ChannelAccess.ALARM_MAJOR)

    def test_GIVEN_motor_at_position_WHEN_set_postion_THEN_motor_moves_to_the_position(self):
        expected_value = 10
        self.set_starting_position(0)
        self.ca.set_pv_value("MTR0101", expected_value)

        self.ca.assert_that_pv_is("MTR0101.RBV", expected_value)

    @skipIf(IOCRegister.uses_rec_sim, "Sim motor doesn't home")
    def test_GIVEN_a_motor_WHEN_homed_THEN_motor_moves_to_home(self):
        expected_home = 0
        self.set_starting_position(10)
        self.ca.set_pv_value("MTR0101.HOMF", 1)

        self.ca.assert_that_pv_is("MTR0101.RBV", expected_home)

    @skipIf(IOCRegister.uses_rec_sim, "Sim motor doesn't home")
    def test_GIVEN_a_motor_WHEN_homed_in_reverse_THEN_motor_moves_to_home(self):
        expected_home = 0
        self.set_starting_position(10)
        self.ca.set_pv_value("MTR0101.HOMR", 1)

        self.ca.assert_that_pv_is("MTR0101.RBV", expected_home)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to get reset values set from lewis")
    def test_GIVEN_a_motor_WHEN_reset_pressed_THEN_initial_values_sent(self):
        self.ioc_ca.wait_for("RESET", 30)
        self.ioc_ca.set_pv_value("RESET", 1)

        reset_codes = self._lewis.backdoor_get_from_device("reset_codes")

        for reset_code in expected_reset_codes:
            assert_that(reset_codes, contains_string(reset_code))
        self.ioc_ca.assert_that_pv_is("RESET", "Done")

    @skipIf(IOCRegister.uses_rec_sim, "Sim doesn't return until move is finished")
    def test_GIVEN_a_motor_moving_to_set_point_WHEN_told_to_move_to_another_set_point_THEN_motor_goes_to_new_setpoint(self):
        self.set_starting_position(0)
        first_position = 20
        final_position = 30
        self.ca.set_pv_value("MTR0101", first_position)
        self.ca.assert_that_pv_is("MTR0101.DMOV", 0)

        self.ca.set_pv_value("MTR0101", final_position)

        self.ca.assert_that_pv_is("MTR0101.RBV", final_position)

    @skipIf(IOCRegister.uses_rec_sim, "Sim doesn't return until move is finished")
    def test_GIVEN_an_axis_moving_to_set_point_WHEN_other_axis_told_to_move_THEN_motor_goes_to_setpoint(self):
        self.set_starting_position(0, axis="x")
        self.set_starting_position(0, axis="y")
        x_position = 10
        y_position = 5
        self.ca.set_pv_value("MTR0101.VAL", x_position)
        self.ca.assert_that_pv_is("MTR0101.DMOV", 0)

        self.ca.set_pv_value("MTR0102.VAL", y_position)

        self.ca.assert_that_pv_is("MTR0101.RBV", x_position)
        self.ca.assert_that_pv_is("MTR0102.RBV", y_position)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to get reset code from lewis")
    def test_GIVEN_a_motor_WHEN_disconnect_THEN_M77_is_sent(self):
        self.ioc_ca.wait_for("DISCONNECT", 30)
        self.ioc_ca.set_pv_value("DISCONNECT", 1)

        reset_codes = self._lewis.backdoor_get_from_device("disconnect")

        assert_that(reset_codes, is_("77"))

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set error code in lewis")
    def test_GIVEN_normal_error_WHEN_query_THEN_error_is_set(self):
        self._lewis.backdoor_set_on_device("error_code", 1)

        self.ioc_ca.assert_that_pv_is("ERROR", "Servo error")
        self.ioc_ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_MAJOR)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set error code in lewis")
    def test_GIVEN_no_error_WHEN_query_THEN_error_is_blank(self):
        self._lewis.backdoor_set_on_device("error_code", 0)

        self.ioc_ca.assert_that_pv_is("ERROR", "")
        self.ioc_ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_NONE)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set error code in lewis")
    def test_GIVEN_command_send_error_WHEN_query_THEN_error_is_set(self):
        self._lewis.backdoor_set_on_device("error_code", 0x10)

        self.ioc_ca.assert_that_pv_is("ERROR", "Cmd error code")
        self.ioc_ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_MAJOR)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set error code in lewis")
    def test_GIVEN_cnc_command_send_CNC_error_WHEN_query_THEN_error_is_set(self):
        self._lewis.backdoor_set_on_device("error_code", 0x20)

        self.ioc_ca.assert_that_pv_is("ERROR", "CNC cmd error code")
        self.ioc_ca.assert_pv_alarm_is("ERROR", ChannelAccess.ALARM_MAJOR)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set error code in lewis")
    def test_GIVEN_a_motor_WHEN_reset_and_homed_THEN_motor_moves_to_home_and_resets(self):
        expected_home = 0
        self.set_starting_position(20, axis="x")
        self.set_starting_position(20, axis="y")

        self.ioc_ca.set_pv_value("RESET_AND_HOME", 1)

        reset_codes = self._lewis.backdoor_get_from_device("reset_codes")
        for reset_code in expected_reset_codes:
            assert_that(reset_codes, contains_string(reset_code))
            self.ioc_ca.assert_that_pv_is("RESET", "Done")
        self.ca.assert_that_pv_is("MTR0101.RBV", expected_home)
        self.ca.assert_that_pv_is("MTR0102.RBV", expected_home)

    @skipIf(IOCRegister.uses_rec_sim, "Needs to set disconnected")
    def test_GIVEN_motor_is_disconnected_WHEN_get_axis_x_ioc_position_THEN_alarm_is_disconnected(self):
        self._lewis.backdoor_set_on_device("is_disconnected", True)

        self.ca.assert_pv_alarm_is("MTR0101", ChannelAccess.ALARM_INVALID)
