import unittest
from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "TTI355_01"
DEVICE_NAME = "tti355"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TTI355"),
        "macros": {},
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
        [1,],
        [2,]
    ])
    def test_WHEN_voltage_is_set_THEN_voltage_setpoint_updates(self, volt):
        self.ca.set_pv_value("VOLTAGE:SP", volt)
        self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", volt)

    @parameterized.expand([
        [0,],
        [0.1,],
        [0.2,]
    ])
    def test_WHEN_current_setpoint_is_set_THEN_current_readback_updates(self, current):
        self.ca.set_pv_value("CURRENT:SP", current)
        self.ca.assert_that_pv_is("CURRENT:SP:RBV", current)

    @parameterized.expand([
        ["ON",],
        ["OFF",]
    ])
    def test_WHEN_outputstatus_is_set_THEN_outputstatus_readback_updates(self, status):
        self.ca.set_pv_value("OUTPUTSTATUS:SP", status)
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", status)
    
    @skip_if_recsim("Relies on emulator logic")
    def test_WHEN_voltage_setpoint_is_set_outside_max_limits_THEN_device_in_error_state(self):
        self.ca.set_pv_value("VOLTAGE:SP", 38.0)
        self.ca.assert_that_pv_is("ERROR", "Cmd outside limits")
    
    @skip_if_recsim("Relies on emulator logic")
    def test_WHEN_current_setpoint_is_set_outside_max_limits_THEN_device_in_error_state(self):
        self.ca.set_pv_value("CURRENT:SP", 7.0)
        self.ca.assert_that_pv_is("ERROR", "Cmd outside limits")
       

    def test_WHEN_identity_requested_THEN_correct_identity_returned(self):
        expected_identity = "THURLBY EX355P, <version>"
        self.ca.assert_that_pv_is("IDENT", expected_identity)

    def test_WHEN_ioc_in_error_state
    xpected_value = 300
        self._lewis.backdoor_set_on_device("pressure", expected_value)

        self.ca.assert_that_pv_is("PRESSURE", expected_value, timeout=1)
    """
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
    """