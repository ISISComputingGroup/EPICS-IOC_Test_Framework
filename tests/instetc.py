import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "INSTETC"

NUM_USER_VARS = 5
NUM_USER_BUTTONS = 5
IOCS = [
    {
        "name": "INSTETC",
        "directory": get_default_ioc_dir("INSTETC"),
        "custom_prefix": "CS",
        "pv_for_existence": "MANAGER",
        "macros": {"NUM_USER_VARS": NUM_USER_VARS, "NUM_USER_BUTTONS": NUM_USER_BUTTONS},
    },
]

TEST_MODES = [TestModes.RECSIM]


class InstEtcTests(unittest.TestCase):
    """
    Tests for instrument etc. ioc
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(ioc_name=DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix="PARS")

    @parameterized.expand([("I", 12), ("R", 12.34), ("S", "123abc")])
    def test_GIVEN_loaded_WHEN_set_and_read_user_integer_THEN_integer_is_set(
        self, test_type, value
    ):
        for var_index in range(NUM_USER_VARS + 1):
            self.ca.assert_setting_setpoint_sets_readback(
                value, readback_pv="USER:{}{}".format(test_type, var_index)
            )
        self.ca.assert_that_pv_does_not_exist("USER:I{}".format(NUM_USER_VARS + 1))

    def test_GIVEN_loaded_WHEN_get_max_user_record_THEN_max_is_returned(self):
        self.ca.assert_that_pv_is("USER:MAX", NUM_USER_VARS)

    def test_GIVEN_loaded_WHEN_get_max_user_buttons_THEN_max_is_returned(self):
        self.ca.assert_that_pv_is("USER:BUTTONS:MAX", NUM_USER_BUTTONS)

    def test_GIVEN_loaded_WHEN_set_and_read_button_THEN_running_set(self):
        for var_index in range(NUM_USER_BUTTONS + 1):
            self.ca.assert_setting_setpoint_sets_readback(
                "Running",
                readback_pv="USER:BUTTON{}:SP".format(var_index),
                set_point_pv="USER:BUTTON{}:SP".format(var_index),
            )
        self.ca.assert_that_pv_does_not_exist("USER:BUTTON{}".format(NUM_USER_VARS + 1))
