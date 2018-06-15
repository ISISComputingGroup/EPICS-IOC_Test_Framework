import unittest
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "SP2XX_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SP2XX"),
        "macros": {},
        "emulator": "sp2xx",
        "emulator_protocol": "stream"
    }
]


TEST_MODES = [TestModes.DEVSIM] #TestModes.RECSIM,


class Sp2XxRunCommandTests(unittest.TestCase):
    """
    Tests for the Sp2XX IOC run command.
    """
    def setUp(self):
        # Given
        self._lewis, self._ioc = get_running_lewis_and_ioc("sp2xx", DEVICE_PREFIX)
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_run_function_on_device("set_running_status_via_the_back_door", ["Stopped"])

    def tearDown(self):
        self._lewis.backdoor_run_function_on_device("set_running_status_via_the_back_door", ["Stopped"])

    def _start_running(self):
        self._lewis.backdoor_run_function_on_device("set_running_status_via_the_back_door", ["Infusing"])

    def test_that_GIVEN_an_initialized_pump_THEN_it_is_stopped(self):
        # Then:
        self.ca.assert_that_pv_is("STATUS", "Stopped")

    def test_that_GIVEN_a_pump_in_infusion_mode_which_is_not_running_THEN_the_pump_starts_running_(self):
        # When
        self._start_running()

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Infusing")

    def test_that_GIVEN_the_pump_is_running_infusion_mode_WHEN_told_to_run_THEN_the_pump_is_still_running_in_infusion_mode(self):
        # Given
        self._start_running()

        # When
        self._start_running()

        # Then:
        self.ca.assert_that_pv_is("STATUS", "Infusing")
