import unittest
from parameterized import parameterized

from common_tests.tti_common import TtiCommon
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "TTIEX355P_01"
DEVICE_NAME = "ttiex355p"

AMPSTOGAUSS = 7.278
MAX_FIELD = 25

# Taken from manual Specification of OUTPUT page 3^M
MIN_VOLTAGE = 0.0
MIN_CURRENT = 0.01
MAX_VOLTAGE = 35.0
MAX_CURRENT = 5.0

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TTIEX355P"),
        "macros": {
            "AMPSTOGAUSS": AMPSTOGAUSS,
            "MAX_FIELD": MAX_FIELD,
            "DISABLE_AUTOONOFF": 0
        },
        "emulator": DEVICE_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Tti355Tests(TtiCommon, unittest.TestCase):
    """
    Tests for the Tti355 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
        self._lewis.backdoor_run_function_on_device("reset")

        self.ca.set_pv_value("AUTOONOFF", "Disabled")

    def get_on_state_name(self):
        return "On"

    def get_off_state_name(self):
        return "Off"

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_identity_requested_THEN_correct_identity_returned(self):
        expected_identity = "Thandar,EL302P,0,v1.14"
        self.ca.assert_that_pv_is("IDENT", expected_identity)

    def _turn_on_in_const_current_mode(self):
        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_set_on_device("output_mode", "M CI")
            self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Current")

        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_on_state_name())

    @parameterized.expand(parameterized_list([MAX_FIELD, 1, 0]))
    def test_WHEN_field_set_THEN_current_setpoint_updates(self, _, field):
        self._turn_on_in_const_current_mode()

        self.ca.set_pv_value("FIELD:SP", field)
        self.ca.assert_that_pv_is_number("CURRENT:SP", field / AMPSTOGAUSS, tolerance=0.08)

        self.ca.assert_that_pv_is_number("CURRENT", field / AMPSTOGAUSS, tolerance=0.08, timeout=30)
        self.ca.assert_that_pv_is_number("CURRENT:SP:RBV", field / AMPSTOGAUSS, tolerance=0.08)

        self.ca.assert_that_pv_is_number("FIELD", field, tolerance=0.08)
        self.ca.assert_that_pv_is_number("FIELD:SP:RBV", field, tolerance=0.08)

        self.ca.assert_that_pv_is("FIELD_READY", "Yes")

    def test_WHEN_field_set_THEN_percentage_of_max_field_is_calculated_correctly(self):
        self._turn_on_in_const_current_mode()

        self.ca.set_pv_value("FIELD:SP", MAX_FIELD / 2)
        self.ca.assert_that_pv_is_number("FIELD:PERCENT", 50, tolerance=0.08)

    def test_WHEN_field_greater_than_max_is_set_THEN_field_is_capped_to_max(self):
        self.ca.set_pv_value("FIELD:SP", MAX_FIELD + 1)
        self.ca.assert_that_pv_is_number("FIELD:SP:RBV", MAX_FIELD, tolerance=0.08)

    def test_WHEN_autoonoff_enabled_then_psu_automatically_switches_on_if_non_zero_setpoint(self):
        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_off_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_off_state_name())

        self.ca.set_pv_value("AUTOONOFF", "Enabled")
        self.ca.set_pv_value("FIELD:SP", MAX_FIELD)

        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_on_state_name(), timeout=60)

    def test_WHEN_autoonoff_enabled_then_psu_automatically_switches_off_if_zero_setpoint(self):
        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_off_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_off_state_name())

        self.ca.set_pv_value("AUTOONOFF", "Enabled")
        self.ca.set_pv_value("FIELD:SP", MAX_FIELD)

        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_on_state_name(), timeout=60)

        self.ca.set_pv_value("FIELD:SP", 0)
        self.ca.assert_that_pv_is_number("CURRENT:SP:RBV", 0, tolerance=0.08)
        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_off_state_name(), timeout=60)

    def test_WHEN_sweep_off_called_THEN_setpoints_set_to_zero_and_power_supply_switched_off(self):
        self._turn_on_in_const_current_mode()

        self.ca.set_pv_value("FIELD:SP", MAX_FIELD)

        self.ca.assert_that_pv_is_number("FIELD", MAX_FIELD, tolerance=0.08)

        self.ca.set_pv_value("SWEEP_OFF", 1)

        self.ca.assert_that_pv_is_number("FIELD", 0, tolerance=0.08)
        self.ca.assert_that_pv_is_number("CURRENT", 0, tolerance=0.08)
        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_off_state_name(), timeout=60)

    @parameterized.expand(parameterized_list([
        ("VOLTAGE", MIN_VOLTAGE - 1.0, MIN_VOLTAGE), ("VOLTAGE", MAX_VOLTAGE + 1.0, MAX_VOLTAGE),
        ("CURRENT", MIN_CURRENT - 1.0, MIN_CURRENT), ("CURRENT", MAX_CURRENT + 1.0, MAX_CURRENT)
    ]))
    def test_WHEN_set_past_limits_THEN_limits_set(self, _, pv, setpoint, expected_val):
        self.ca.set_pv_value(f"{pv}:SP", setpoint)
        self.ca.assert_that_pv_is_number(f"{pv}:SP:RBV", expected_val, tolerance=0.08)
