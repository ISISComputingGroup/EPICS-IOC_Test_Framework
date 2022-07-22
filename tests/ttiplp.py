import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "TTIPLP_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TTIPLP"),
        "macros": {},
        "emulator": "ttiplp",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class TtiplpTests(unittest.TestCase):
    """
    Tests for the Ttiplp IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("ttiplp", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=5)
        self._lewis.backdoor_run_function_on_device("reset")
        
    def set_init_state(self, volt_sp=0., curr_sp=0., ov_volt_sp=0., ov_curr_sp=0., output="Off"):
        self.ca.set_pv_value("OUTPUT:SP", "Off")
        self.ca.set_pv_value("OVERCURR:SP", ov_curr_sp)
        self.ca.set_pv_value("OVERVOLT:SP", ov_volt_sp)
        self.ca.set_pv_value("CURRENT:SP", curr_sp)
        self.ca.set_pv_value("VOLTAGE:SP", volt_sp)
        self.ca.set_pv_value("OUTPUT:SP", output)

    def test_WHEN_voltage_setpoint_is_set_THEN_voltage_readback_updates(self):
        for volt in [0, 1, 2]:
            self.ca.set_pv_value("VOLTAGE:SP", volt)
            self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", volt)

    def test_WHEN_current_setpoint_is_set_THEN_current_readback_updates(self):
        for curr in [0, 0.1, 0.2]:
            self.ca.set_pv_value("CURRENT:SP", curr)
            self.ca.assert_that_pv_is("CURRENT:SP:RBV", curr)
            
    def test_GIVEN_overvolt_and_overcurrent_more_than_output_current_and_output_voltage_WHEN_output_set_THEN_output_readback_updates(self):
        self.set_init_state(1, 0.01, 10, 0.1, "Off")
        self.ca.assert_that_pv_is("OUTPUT", "Off")
        for state in ["Off", "On", "Off"]:
            self.ca.set_pv_value("OUTPUT:SP", state)
            self.ca.assert_that_pv_is("OUTPUT", state)
            
    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_GIVEN_overvolt_and_overcurrent_more_than_output_current_and_output_voltage_WHEN_overvolt_set_less_than_output_voltage_THEN_output_readback_turns_off(self):
        self.set_init_state(10, 0.01, 20, 0.1, "On")
        self.ca.assert_that_pv_is("OUTPUT", "On")
        self.ca.set_pv_value("OVERVOLT:SP", 8)
        self.ca.assert_that_pv_is("OVERVOLT:SP:RBV", 8)
        self.ca.assert_that_pv_is("OUTPUT", "Off")
    
    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_GIVEN_overvolt_and_overcurrent_more_than_output_current_and_output_voltage_WHEN_overcurrent_set_less_than_output_current_THEN_output_readback_turns_off(self):
        self.set_init_state(10, 0.1, 20, 1, "On")
        self.ca.assert_that_pv_is("OUTPUT", "On")
        self.ca.set_pv_value("OVERCURR:SP", 0.05)
        self.ca.assert_that_pv_is("OVERCURR:SP:RBV", 0.05)
        self.ca.assert_that_pv_is("OUTPUT", "Off")
        
    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_GIVEN_overvolt_and_overcurrent_less_than_output_current_and_output_voltage_WHEN_output_set_to_on_THEN_output_readback_stays_off(self):
        self.set_init_state(10, 0.1, 10, 0.01, "Off")
        self.ca.assert_that_pv_is("OUTPUT", "Off")
        for state in ["Off", "On", "Off"]:
            self.ca.set_pv_value("OUTPUT:SP", state)
            self.ca.assert_that_pv_is("OUTPUT", "Off")
            
    def test_WHEN_over_voltage_setpoint_is_set_THEN_over_voltage_readback_updates(self):
        for volt in [0, 1, 2]:
            self.ca.set_pv_value("OVERVOLT:SP", volt)
            self.ca.assert_that_pv_is("OVERVOLT:SP:RBV", volt)

    def test_WHEN_over_current_setpoint_is_set_THEN_over_current_readback_updates(self):
        for curr in [0, 0.1, 0.2]:
            self.ca.set_pv_value("OVERCURR:SP", curr)
            self.ca.assert_that_pv_is("OVERCURR:SP:RBV", curr)

    def test_GIVEN_set_output_conditions_WHEN_the_output_is_on_THEN_readback_voltage_is_close_to_the_voltage_setpoint(self):
        self.set_init_state(10, 0.1, 20, 1, "On")
        self.ca.assert_that_pv_is("OUTPUT", "On")
        for volt in [0, 5, 10]:
            self.ca.set_pv_value("VOLTAGE:SP", volt)
            self.ca.assert_that_pv_is("OUTPUT", "On")
            self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", volt)
            self.ca.assert_that_pv_is_number("VOLTAGE", volt, tolerance=0.1)

    def test_GIVEN_set_output_conditions_WHEN_the_output_is_on_THEN_readback_current_is_close_to_the_current_setpoint(self):
        self.set_init_state(10, 0.1, 20, 1, "On")
        self.ca.assert_that_pv_is("OUTPUT", "On")
        for curr in [0, 0.1, 0.2]:
            self.ca.set_pv_value("CURRENT:SP", curr)
            self.ca.assert_that_pv_is("OUTPUT", "On")
            self.ca.assert_that_pv_is("CURRENT:SP:RBV", curr)
            self.ca.assert_that_pv_is_number("CURRENT", curr, tolerance=0.01)
   
    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_GIVEN_normal_operation_THEN_limit_event_staus_bits_are_not_set(self):
        self.set_init_state(volt_sp=10., curr_sp=1., ov_volt_sp=15., ov_curr_sp=2., output="On")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Ok")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Ok")

    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_WHEN_voltage_higher_than_overvolt_protection_limit_THEN_overvolt_status_set_to_tripped(self):
        self.set_init_state(volt_sp=10., curr_sp=1., ov_volt_sp=5., ov_curr_sp=2., output="On")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Ok")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Tripped")

    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_WHEN_current_higher_than_overcurr_protection_limit_THEN_overcurr_status_set_to_tripped(self):
        self.set_init_state(volt_sp=10., curr_sp=2., ov_volt_sp=20., ov_curr_sp=1, output="On")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Tripped")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Ok")

    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_WHEN_current_and_voltage_higher_than_protection_limits_THEN_both_statuses_set_to_tripped(self):
        self.set_init_state(volt_sp=10., curr_sp=2., ov_volt_sp=5., ov_curr_sp=1, output="On")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Tripped")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Tripped")

    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_GIVEN_overvolt_tripped_WHEN_triprst_called_THEN_overvolt_ok(self):
        self.set_init_state(volt_sp=10., curr_sp=1., ov_volt_sp=5., ov_curr_sp=2., output="On")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Ok")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Tripped")

        self.ca.process_pv("TRIPRST")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Ok")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Ok")

    @skip_if_recsim("Behaviour not modelled in recsim")
    def test_GIVEN_overcurr_tripped_WHEN_triprst_called_THEN_overcurr_ok(self):
        self.set_init_state(volt_sp=10., curr_sp=3., ov_volt_sp=15., ov_curr_sp=2., output="On")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Tripped")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Ok")

        self.ca.process_pv("TRIPRST")

        self.ca.assert_that_pv_is("OVERCURR:STAT", "Ok")
        self.ca.assert_that_pv_is("OVERVOLT:STAT", "Ok")
