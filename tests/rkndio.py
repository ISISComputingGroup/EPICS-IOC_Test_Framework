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

# Kathryn confirmed she is happy with the tests only running in devsim.
TEST_MODES = [TestModes.DEVSIM]


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

        self._lewis.backdoor_run_function_on_device("reset_error")

        self.ca.assert_that_pv_is("STATUS", "No error")
        self.ca.assert_that_pv_is("ERROR", "No error")

    def _connect_emulator(self):
        self._lewis.backdoor_run_function_on_device("connect")

    def _disconnect_emulator(self):
        self._lewis.backdoor_run_function_on_device("disconnect")

    def test_that_we_can_receive_the_correct_IDN(self):
        # When:
        self.ca.process_pv("IDN")

        # Then:
        self.ca.assert_that_pv_is("IDN", "RIKENFE Prototype v2.0")

    @skip_if_recsim("Recsim is unable to simulate a disconnected device")
    def test_that_GIVEN_a_disconnected_emulator_WHEN_getting_pressure_THEN_INVALID_alarm_shows(
        self,
    ):
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
        error_message = "The pin is not readable"
        self._lewis.backdoor_set_on_device("error", error_message)

        # When/Then:
        self.ca.assert_that_pv_is("ERROR", error_message)

    @parameterized.expand([("Pin_{}".format(i), i) for i in range(2, 8)])
    def test_that_we_can_read_a_digital_input(self, _, pin):
        # Given
        pv = "PIN:{}".format(pin)
        self._lewis.backdoor_run_function_on_device(
            "set_input_state_via_the_backdoor", [pin, "FALSE"]
        )
        self.ca.assert_that_pv_is(pv, "FALSE")

        self._lewis.backdoor_run_function_on_device(
            "set_input_state_via_the_backdoor", [pin, "TRUE"]
        )

        # When:
        self.ca.process_pv(pv)

        # Then:
        self.ca.assert_that_pv_is(pv, "TRUE")

    @parameterized.expand([("Pin_{}".format(i), i) for i in range(8, 14)])
    def test_that_we_can_write_to_a_digital_output(self, _, pin):
        # Given
        pv = "PIN:{}".format(pin)
        self.ca.set_pv_value(pv, "FALSE")
        reset_check = self._lewis.backdoor_run_function_on_device(
            "get_output_state_via_the_backdoor", [pin]
        )[0]
        self.assertEqual(reset_check, b"FALSE")

        # When:
        self.ca.set_pv_value(pv, "TRUE")

        # Then:
        result = self._lewis.backdoor_run_function_on_device(
            "get_output_state_via_the_backdoor", [pin]
        )[0]
        self.assertEqual(result, b"TRUE")
