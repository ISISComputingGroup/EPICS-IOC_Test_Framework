import unittest

from parameterized import parameterized

from common_tests.tti_common import TtiCommon
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


class Tti355Tests(TtiCommon, unittest.TestCase):
    """
    Tests for the Tti355 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("reset")

    def get_on_state_name(self):
        return "ON"

    def get_off_state_name(self):
        return "OFF"

    @parameterized.expand(
        [
            ("lt_low_limit", VOLT_LOW_LIMIT - 1.0, "low_limit", VOLT_LOW_LIMIT),
            ("gt_high_limit", VOLT_HIGH_LIMIT + 1, "high_limit", VOLT_HIGH_LIMIT),
        ]
    )
    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_voltage_setpoint_is_set_outside_max_limits_THEN_setpoint_within(
        self, case, case_value, limit, limit_value
    ):
        self.ca.set_pv_value("VOLTAGE:SP", case_value)
        self.ca.assert_that_pv_is("VOLTAGE:SP", limit_value)

    @parameterized.expand(
        [
            ("lt_low_limit", CURR_LOW_LIMIT - 1, "low_limit", CURR_LOW_LIMIT),
            ("gt_high_limit", CURR_HIGH_LIMIT + 1, "high_limit", CURR_HIGH_LIMIT),
        ]
    )
    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_voltage_setpoint_is_set_outside_max_limits_THEN_setpoint_within(
        self, case, case_value, limit, limit_value
    ):
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
