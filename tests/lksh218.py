import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
from lewis.core.logging import has_log


DEVICE_PREFIX = "LKSH218_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LKSH218"),
        "macros": {},
        "emulator": "Lksh218",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


@has_log
class Lksh218Tests(unittest.TestCase):
    """
    Tests for the Lksh218 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Lksh218", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def _set_temperature(self, number, temperature):
        pv = "SIM:TEMP{}".format(number)
        self._lewis.backdoor_run_function_on_device("set_temp", [number, temperature])
        self._ioc.set_simulated_value(pv, temperature)

    def _set_sensor(self, number, value):
        pv = "SIM:SENSOR{}".format(number)
        self._lewis.backdoor_run_function_on_device("set_sensor", [number, value])
        self._ioc.set_simulated_value(pv, value)

    def test_WHEN_ioc_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_that_GIVEN_temp_float_WHEN_temp_pvs_are_read_THEN_temp_is_as_expected(self):
        expected_value = 10.586

        for index in range(1, 9):
            pv = "TEMP{}".format(index)
            self._set_temperature(index, expected_value)
            self.ca.assert_that_pv_is(pv, expected_value)

    def test_that_GIVEN_sensor_float_WHEN_sensor_pvs_are_read_THEN_sensor_is_as_expected(self):
        expected_value = 11.386

        for index in range(1, 9):
            pv = "SENSOR{}".format(index)
            self._set_sensor(index, expected_value)
            self.ca.assert_that_pv_is(pv, expected_value)
