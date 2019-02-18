import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim


DEVICE_PREFIX = "LKSH218_04"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LKSH218", iocnum=4),
        "macros": {},
        "emulator": "Lksh218",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Lksh218Tests(unittest.TestCase):
    """
    Tests for the Lksh218 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Lksh218", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("connected", True)

    def tearDown(self):
        self._lewis.backdoor_set_on_device("connected", True)

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

    def test_that_WHEN_reading_all_temps_pv_THEN_all_temp_pv_are_as_expected(self):
        expected_string = "10.4869"
        self._lewis.backdoor_set_on_device("temp_all", expected_string)
        self._ioc.set_simulated_value("SIM:TEMPALL", expected_string)

        self.ca.process_pv("TEMPALL")
        self.ca.assert_that_pv_is("TEMPALL", expected_string)

    def test_that_WHEN_reading_sensor_all_pv_THEN_sensor_all_pv_returns_as_expected(self):
        expected_string = "12.129"
        self._lewis.backdoor_set_on_device("sensor_all", expected_string)
        self._ioc.set_simulated_value("SIM:SENSORALL", expected_string)

        self.ca.process_pv("SENSORALL")
        self.ca.assert_that_pv_is("SENSORALL", expected_string)

    @skip_if_recsim("Recsim is unable to simulate a disconnected device.")
    def test_that_WHEN_the_emulator_is_disconnected_THEN_an_alarm_is_raised_on_TEMP_and_SENSOR(self):
        self._lewis.backdoor_set_on_device("connected", False)

        for i in range(1, 9):
            self.ca.assert_that_pv_alarm_is("TEMP{}".format(i), ChannelAccess.Alarms.INVALID)
            self.ca.assert_that_pv_alarm_is("SENSOR{}".format(i), ChannelAccess.Alarms.INVALID)

    @skip_if_recsim("Recsim is unable to simulate a disconnected device.")
    def test_that_WHEN_the_emulator_is_disconnected_THEN_an_alarm_is_raised_on_SENSORALL(self):
        self._lewis.backdoor_set_on_device("connected", False)

        self.ca.process_pv("SENSORALL")
        self.ca.assert_that_pv_alarm_is("SENSORALL", ChannelAccess.Alarms.INVALID)

    @skip_if_recsim("Recsim is unable to simulate a disconnected device.")
    def test_that_WHEN_the_emulator_is_disconnected_THEN_an_alarm_is_raised_on_TEMPALL(self):
        self._lewis.backdoor_set_on_device("connected", False)

        self.ca.process_pv("TEMPALL")
        self.ca.assert_that_pv_alarm_is("TEMPALL", ChannelAccess.Alarms.INVALID)
