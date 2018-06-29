import unittest
from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "RKNDIO_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("RKNDIO"),
        "macros": {},
        "emulator": "rkndio",
    },
]


TEST_MODES = [TestModes.DEVSIM] #, TestModes.RECSIM]


class RkndioVersionTests(unittest.TestCase):
    """
    Tests for the Rkndio IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("rkndio", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._reset_device()

    def _reset_device(self):
        self._connect_emulator()
        self.ca.assert_that_pv_exists("IDN")

        self._lewis.backdoor_set_on_device("status", "No Error")
        self.ca.assert_that_pv_is("STATUS", "No Error")

        self._lewis.backdoor_set_on_device("error", "No Error")
        self.ca.assert_that_pv_is("ERROR", "No Error")

    def _connect_emulator(self):
        self._lewis.backdoor_run_function_on_device("connect")

    def _disconnect_emulator(self):
        self._lewis.backdoor_run_function_on_device("disconnect")

    def test_that_we_can_receive_the_correct_IDN(self):
        # When:
        self.ca.process_pv("IDN")

        # Then:
        self.ca.assert_that_pv_is("IDN", "RIKENFE Prototype v2.0", timeout=100)

    @skip_if_recsim("Recsim is unable to simulate a disconnected device")
    def test_that_GIVEN_a_disconnected_emulator_WHEN_getting_pressure_THEN_INVALID_alarm_shows(self):
        # Given:
        self._disconnect_emulator()

        # When:
        self.ca.process_pv("IDN")

        # Then:
        self.ca.assert_that_pv_alarm_is("IDN", self.ca.Alarms.INVALID)

    def test_that_we_can_get_the_status_of_the_device(self):
        # Given
        status_message = "A Status"
        self._lewis.backdoor_set_on_device("status", status_message)

        # When/Then:
        self.ca.assert_that_pv_is("STATUS", status_message)

    def test_that_we_can_get_the_error_status_of_the_device(self):
        # Given:
        error_message = "Some Error"
        self._lewis.backdoor_set_on_device("error", error_message)

        # When/Then:
        self.ca.assert_that_pv_is("ERROR", error_message)

    @parameterized.expand([
        ("Pin_{}".format(i), i) for i in range(2, 8)
    ])
    def test_that_we_can_read_a_digital_input(self, _, pin):
        # Given
        pv = "PIN_{}".format(pin)
        self._lewis.backdoor_run_function_on_device("set_input_state_via_the_backdoor", [pin, "False"])
        self.ca.assert_that_pv_is(pv, "False")

        self._lewis.backdoor_run_function_on_device("set_input_state_via_the_backdoor", [pin, "True"])

        # When:
        self.ca.process_pv(pv)

        # Then:
        self.ca.assert_that_pv_is(pv, "True")

    @parameterized.expand([
        ("Pin_{}".format(i), i) for i in range(8, 14)
    ])
    def test_that_we_can_write_to_a_digital_output(self, _, pin):
        # Given
        pv = "PIN_{}".format(pin)
        self.ca.set_pv_value(pv, "FALSE")
        reset_check = self._lewis.backdoor_run_function_on_device("get_output_state_via_the_backdoor", [pin])[0]
        self.assertEqual(reset_check, "False")

        # When:
        self.ca.set_pv_value(pv, "TRUE")

        # Then:
        result = self._lewis.backdoor_run_function_on_device("get_output_state_via_the_backdoor", [pin])[0]
        self.assertEqual(result, "True")

