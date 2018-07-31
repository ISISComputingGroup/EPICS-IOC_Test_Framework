import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "OMIBTHX_01"
EMULATOR_NAME = "omibthx"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("OMIBTHX"),
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

TEST_VALUES = [0, 12345.6, 1.23, -5]


class OmibthxTests(unittest.TestCase):
    """
    Tests for the Omibthx IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=20)

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_device_has_a_humidity_reading_WHEN_polling_for_humidity_THEN_correct_reading_is_returned(self):
        for number in TEST_VALUES:
            self._lewis.backdoor_set_on_device("humidity", number)
            self.ca.assert_that_pv_is_number("HUMIDITY", number, tolerance=0.1)  # device rounds to 1 d.p

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_device_has_temperature_reading_WHEN_polling_for_temperature_THEN_correct_reading_is_returned(self):
        for number in TEST_VALUES:
            self._lewis.backdoor_set_on_device("temperature", number)
            self.ca.assert_that_pv_is_number("TEMP", number, tolerance=0.01)  # device rounds to 2 d.p

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_device_has_pressure_reading_WHEN_polling_for_pressure_THEN_correct_reading_is_returned(self):
        for number in TEST_VALUES:
            self._lewis.backdoor_set_on_device("pressure", number)
            self.ca.assert_that_pv_is_number("PRESSURE", number, tolerance=0.01)  # device rounds to 2 d.p

    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_GIVEN_device_has_dewpoint_reading_WHEN_polling_for_dewpoint_THEN_correct_reading_is_returned(self):
        for number in TEST_VALUES:
            self._lewis.backdoor_set_on_device("dew_point", number)
            self.ca.assert_that_pv_is_number("DEWPOINT", number, tolerance=0.01)  # device rounds to 2 d.p
