import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "KYNCTM3K_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KYNCTM3K"),
        "macros": {},
        "emulator": "Kynctm3K",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Kynctm3KTests(unittest.TestCase):
    """
    Tests for the Keyence TM-3001P IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Kynctm3K", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_that_fails(self):
        self.fail("You haven't implemented any tests!")

    def test_WHEN_head_configuration_is_set_THEN_device_updates_to_given_setup(self):
        for screen_type in [0, 16, "HA"]:
            self.ca.set_pv_value(screen_type, "MEAS:SCREEN")
            self.ca.assert_that_pv_is("MEAS:SCREEN", screen_type)

    @skip_if_recsim("Backdoor behaviour too complex for RECSIM")
    def test_GIVEN_input_program_WHEN_measurement_value_is_requested_THEN_appropriate_number_of_output_values_are_returned(self):
        for program in ["none", "all", "only_first", "even_numbers"]:
            self._lewis.backdoor_set_on_device("program", program)

