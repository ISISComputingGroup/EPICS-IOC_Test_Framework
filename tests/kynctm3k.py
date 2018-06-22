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

    # defines program modes
    program_modes = {"none": [],
                     "only_first": [0, ],
                     "all": range(1, 17),
                     "even_numbers": [2*x for x in range(1, 9)]}

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Kynctm3K", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

        for channel in range(16):
            self._lewis.backdoor_set_on_device("OUT{}_value".format(channel), 0.)
            self._lewis.backdoor_set_on_device("program", "none")

    @skip_if_recsim("Backdoor behaviour too complex for RECSIM")
    def test_GIVEN_input_program_WHEN_measurement_value_is_requested_THEN_appropriate_number_of_output_values_are_returned(self):

        for program in self.program_modes:

            expected_values = []
            # Assign test values to only the active OUTs in the emulator
            for channel_to_set in range(16):

                if channel_to_set in self.program_modes[program]:
                    channel_value = 2.*channel_to_set
                else:
                    channel_value = False

                expected_values.append(channel_value)

                self._lewis.backdoor_set_on_device("OUT{}_value".format(channel_to_set), channel_value)

            # Read in the measurement values just set
            for channel_to_test, expected_value in enumerate(expected_values):
                if not expected_value:
                    continue

                self.ca.assert_that_pv_is_number("MEAS:OUT{}".format(channel_to_test),
                                                 expected_value, tolerance=0.01*expected_value)

    def test_WHEN_head_configuration_is_set_THEN_device_updates_to_given_setup(self):
        for screen_type in [0, 15, "HA"]:
            self.ca.set_pv_value(screen_type, "MEAS:SCREEN")
            self.ca.assert_that_pv_is("MEAS:SCREEN", screen_type)

