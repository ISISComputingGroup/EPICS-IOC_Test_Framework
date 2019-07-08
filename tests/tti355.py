import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "TTI355_01"
DEVICE_NAME = "tti355"

VOLT_LOW_LIMIT = 0.0
VOLT_HIGH_LIMIT = 35.0
CURR_LOW_LIMIT = 0.01
CURR_HIGH_LIMIT = 5.0

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TTI355"),
        "macros": {
            "MIN_VOLT": VOLT_LOW_LIMIT,
            "MAX_VOLT": VOLT_HIGH_LIMIT,
            "MIN_CURR": CURR_LOW_LIMIT,
            "MAX_CURR": CURR_HIGH_LIMIT,
        },
        "emulator": DEVICE_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tti355Tests(unittest.TestCase):
    """
    Tests for the Tti355 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset")

    @parameterized.expand([
        [0],
        [1],
        [2]
    ])
    def test_WHEN_voltage_is_set_THEN_voltage_setpoint_updates(self, volt):
        self.ca.set_pv_value("VOLTAGE:SP", volt)
        self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", volt)

    @parameterized.expand([
        [0.01],
        [1.30],
        [5.0]
    ])
    def test_WHEN_current_setpoint_is_set_THEN_current_readback_updates(self, current):
        self.ca.set_pv_value("CURRENT:SP", current)
        self.ca.assert_that_pv_is("CURRENT:SP:RBV", current)

    @parameterized.expand([
        ["ON"],
        ["OFF"]
    ])
    def test_WHEN_outputstatus_is_set_THEN_outputstatus_readback_updates(self, status):
        self.ca.set_pv_value("OUTPUTSTATUS:SP", status)
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", status)

    @parameterized.expand([
        ("lt_low_limit", VOLT_LOW_LIMIT-1.0, "low_limit", VOLT_LOW_LIMIT),
        ("gt_high_limit", VOLT_HIGH_LIMIT+1, "high_limit", VOLT_HIGH_LIMIT)])
    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_voltage_setpoint_is_set_outside_max_limits_THEN_setpoint_within(self, case, case_value, limit, limit_value):
        self.ca.set_pv_value("VOLTAGE:SP", case_value)
        self.ca.assert_that_pv_is("VOLTAGE:SP", limit_value)

    @parameterized.expand([
        ("lt_low_limit", CURR_LOW_LIMIT-1, "low_limit", CURR_LOW_LIMIT),
        ("gt_high_limit", CURR_HIGH_LIMIT+1, "high_limit", CURR_HIGH_LIMIT)])
    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_voltage_setpoint_is_set_outside_max_limits_THEN_setpoint_within(self, case, case_value, limit, limit_value):
        self.ca.set_pv_value("CURRENT:SP", case_value)
        self.ca.assert_that_pv_is("CURRENT:SP", limit_value)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_identity_requested_THEN_correct_identity_returned(self):
        expected_identity = "Thurlby Thandar,EL302P,0,v1.14"
        self.ca.assert_that_pv_is("IDENT", expected_identity)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_ioc_in_error_state_2_THEN_correct_error_state_returned(self):
        expected_value = "Cmd outside limits"
        self._lewis.backdoor_set_on_device("error", "ERR 2")
        self.ca.set_pv_value("ERROR.PROC", 1)
        self.ca.assert_that_pv_is("ERROR", expected_value)
    
    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_ioc_not_in_error_state_THEN_correct_error_state_returned(self):
        expected_value = "No error"
        self.ca.set_pv_value("CURRENT:SP", 3.0)
        self.ca.assert_that_pv_is("ERROR", expected_value)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_ioc_in_constant_current_mode_THEN_correct_mode_returned(self):
        expected_value = "Constant Current"
        self._lewis.backdoor_set_on_device("output_mode", "M CI")
        self.ca.assert_that_pv_is("OUTPUTMODE", expected_value)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_ioc_in_constant_voltage_mode_THEN_correct_mode_returned(self):
        expected_value = "Constant Voltage"
        self._lewis.backdoor_set_on_device("output_mode", "M CV")
        self.ca.assert_that_pv_is("OUTPUTMODE", expected_value)

    @parameterized.expand([
        [0],
        [5],
        [10]
    ])
    def test_GIVEN_set_output_conditions_WHEN_the_output_is_on_THEN_readback_voltage_is_close_to_the_voltage_setpoint(self, voltage):

        self.ca.set_pv_value("OUTPUTSTATUS:SP", "ON")
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", "ON")
        self.ca.set_pv_value("VOLTAGE:SP", voltage)
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", "ON")
        self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", voltage)
        self.ca.assert_that_pv_is_number("VOLTAGE", voltage, tolerance=0.1)

    @parameterized.expand([
        [0.01],
        [1.30],
        [5.0]
    ])
    def test_GIVEN_set_output_conditions_WHEN_the_output_is_on_THEN_readback_current_is_close_to_the_current_setpoint(self, current):
        self.ca.set_pv_value("OUTPUTSTATUS:SP", "ON")
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", "ON")
        self._lewis.backdoor_set_on_device("output_mode", "M CI")
        self.ca.set_pv_value("CURRENT:SP", current)
        self.ca.assert_that_pv_is("CURRENT:SP:RBV", current)
        self.ca.assert_that_pv_is_number("CURRENT", current, tolerance=0.01)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_GIVEN_voltage_WHEN_current_limit_is_lower_than_potential_current_and_output_is_on_THEN_mode_is_CI_and_voltage_is_actual(self):
        expected_voltage = 20
        self.ca.set_pv_value("OUTPUTSTATUS:SP", "ON")
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", "ON")
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self._lewis.backdoor_set_on_device("load_resistance", 8.00)
        self.ca.set_pv_value("CURRENT:SP", 2.5)
        self.ca.set_pv_value("VOLTAGE:SP", 25)
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Current")
        self.ca.assert_that_pv_is("VOLTAGE", expected_voltage)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_GIVEN_voltage_WHEN_current_limit_is_lower_than_potential_current_but_output_off_THEN_mode_is_CV_and_voltage_is_not_actual(self):
        expected_voltage = 0
        self.ca.set_pv_value("OUTPUTSTATUS:SP", "OFF")
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", "OFF")
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self._lewis.backdoor_set_on_device("load_resistance", 8.00)
        self.ca.set_pv_value("CURRENT:SP", 2.5)
        self.ca.set_pv_value("VOLTAGE:SP", 25)
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self.ca.assert_that_pv_is("VOLTAGE", expected_voltage)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_GIVEN_voltage_WHEN_current_limit_is_lower_than_potential_current_but_output_off_THEN_mode_is_CV_and_voltage_is_not_actual_but_close_to_sp(self):
        expected_voltage = 10
        self.ca.set_pv_value("OUTPUTSTATUS:SP", "ON")
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", "ON")
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self._lewis.backdoor_set_on_device("load_resistance", 8.00)
        self.ca.set_pv_value("CURRENT:SP", 2.5)
        self.ca.set_pv_value("VOLTAGE:SP", expected_voltage)
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self.ca.assert_that_pv_is_number("VOLTAGE", expected_voltage, tolerance=0.1)
