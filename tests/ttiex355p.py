import unittest
from parameterized import parameterized

from common_tests.tti_common import TtiCommon
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "TTIEX355P_01"
DEVICE_NAME = "tti355"

VOLT_LOW_LIMIT = 0.0
VOLT_HIGH_LIMIT = 35.0
CURR_LOW_LIMIT = 0.01
CURR_HIGH_LIMIT = 5.0

AMPSTOGAUSS = 5
MAX_FIELD = 10

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TTIEX355P"),
        "macros": {
            "AMPSTOGAUSS": AMPSTOGAUSS,
            "MAX_FIELD": MAX_FIELD,
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
        return "On"

    def get_off_state_name(self):
        return "Off"

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_identity_requested_THEN_correct_identity_returned(self):
        expected_identity = "Thandar,EL302P,0,v1.14"
        self.ca.assert_that_pv_is("IDENT", expected_identity)

    @parameterized.expand(parameterized_list([MAX_FIELD, 1, 0]))
    def test_WHEN_field_set_THEN_current_setpoint_updates(self, _, field):
        if not IOCRegister.uses_rec_sim:
            self._lewis.backdoor_set_on_device("output_mode", "M CI")
            self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Current")

        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS", self.get_on_state_name())

        self.ca.set_pv_value("FIELD:SP", field)
        self.ca.assert_that_pv_is_number("CURRENT:SP", field / AMPSTOGAUSS, tolerance=0.01)

        self.ca.assert_that_pv_is_number("CURRENT", field / AMPSTOGAUSS, tolerance=0.01, timeout=30)
        self.ca.assert_that_pv_is_number("CURRENT:SP:RBV", field / AMPSTOGAUSS, tolerance=0.01)

        self.ca.assert_that_pv_is_number("FIELD", field, tolerance=0.01)
        self.ca.assert_that_pv_is_number("FIELD:SP:RBV", field, tolerance=0.01)