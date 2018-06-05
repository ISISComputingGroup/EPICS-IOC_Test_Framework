import unittest
from time import sleep

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc, assert_log_messages, skip_if_recsim

# Device prefix
DEVICE_A_PREFIX = "CCD100_01"
DEVICE_E_PREFIX = "CCD100_02"
EMULATOR_NAME = "CCD100"

IOCS = [
    {
        "name": DEVICE_A_PREFIX,
        "directory": get_default_ioc_dir("CCD100"),
        "emulator": EMULATOR_NAME,
    },

    {
        "name": DEVICE_E_PREFIX,
        "directory": get_default_ioc_dir("CCD100", iocnum=2),
        "emulator": EMULATOR_NAME,
        "macros": {"ADDRESS": "e"}
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class CCD100Tests(unittest.TestCase):
    """
    Tests for the CCD100.
    """

    NUM_OF_PVS = 3

    def set_up(self, device=DEVICE_A_PREFIX):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, device)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self._lewis.backdoor_set_on_device("out_error", "OLD_ERROR")
        self._set_error_state(False)

        self.ca = ChannelAccess(device_prefix=device)

    def _set_error_state(self, state):
        self._lewis.backdoor_set_on_device("is_giving_errors", state)
        sleep(2)  # Wait for previous errors to get logged

    def _test_setpoint_and_readback(self):
        set_point = [0, 1.23, 10]
        for point in set_point:
            self.ca.set_pv_value("READING:SP", point)
            self.ca.assert_that_pv_is("READING:SP:RBV", point)

    def test_GIVEN_setpoint_set_for_diff_address_WHEN_readback_THEN_readback_is_same_as_setpoint(self):
        self.set_up(device=DEVICE_E_PREFIX)
        self._lewis.backdoor_set_on_device("address", "e")
        self._test_setpoint_and_readback()

    def test_GIVEN_setpoint_set_WHEN_readback_THEN_readback_is_same_as_setpoint(self):
        self.set_up()
        self._test_setpoint_and_readback()

    # @skip_if_recsim("In rec sim this test fails")
    # def test_GIVEN_not_in_error_WHEN_put_in_error_THEN_three_log_messages_per_pv_logged_in_five_secs(self):
    #     self.set_up()
    #     with assert_log_messages(self._ioc, self.NUM_OF_PVS*3, 5) as log:
    #         self._set_error_state(True)
    #
    # @skip_if_recsim("In rec sim this test fails")
    # def test_GIVEN_in_error_WHEN_error_cleared_THEN_one_log_message_per_pv_logged(self):
    #     self.set_up()
    #     self._set_error_state(True)
    #     with assert_log_messages(self._ioc, self.NUM_OF_PVS*1):
    #         self._set_error_state(False)
    #
    # @skip_if_recsim("In rec sim this test fails")
    # def test_GIVEN_in_error_WHEN_error_string_changed_THEN_three_log_message_per_pv_logged_in_five_secs(self):
    #     self.set_up()
    #     new_error = "A_NEW_ERROR"
    #     self._set_error_state(True)
    #     with assert_log_messages(self._ioc, self.NUM_OF_PVS*3, 5) as log:
    #         self._lewis.backdoor_set_on_device("out_error", new_error)
    #
    #     self.assertTrue(new_error in log.messages[-1])
