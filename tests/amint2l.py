import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

# Internal Address of device (must be 2 characters)
ADDRESS = "01"

# Device prefix
DEVICE_PREFIX = "AMINT2L_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("AMINT2L"),
        "macros": {
            "ADDR": ADDRESS,
        },
        "emulator": "amint2l",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Amint2lTests(unittest.TestCase):
    """
    Tests for the AM Int2-L.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("amint2l", DEVICE_PREFIX)
        self.assertIsNotNone(self._lewis)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("connected", True)
        self._lewis.backdoor_set_on_device("address", ADDRESS)
        self._lewis.backdoor_set_on_device("pressure", 0.0)

    def _set_pressure(self, expected_pressure):
        self._lewis.backdoor_set_on_device("pressure", expected_pressure)
        self._ioc.set_simulated_value("SIM:PRESSURE", expected_pressure)

    def test_GIVEN_pressure_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure)

        self.ca.assert_that_pv_is("PRESSURE", expected_pressure)
        self.ca.assert_that_pv_alarm_is("PRESSURE", self.ca.Alarms.NONE)
        self.ca.assert_that_pv_is("RANGE:ERROR", "No Error")

    def test_GIVEN_negative_pressure_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = -123.34
        self._set_pressure(expected_pressure)

        self.ca.assert_that_pv_is("PRESSURE", expected_pressure)

    def test_GIVEN_pressure_with_no_decimal_places_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 7
        self._set_pressure(expected_pressure)

        self.ca.assert_that_pv_is("PRESSURE", expected_pressure)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_pressure_over_range_set_WHEN_read_THEN_error(self):
        expected_pressure = "OR"
        self._set_pressure(expected_pressure)

        self.ca.assert_that_pv_alarm_is("PRESSURE", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("RANGE:ERROR", "Over Range")

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_pressure_under_range_set_WHEN_read_THEN_error(self):
        expected_pressure = "UR"
        self._set_pressure(expected_pressure)

        self.ca.assert_that_pv_alarm_is("PRESSURE", self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_is("RANGE:ERROR", "Under Range")

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_device_disconnected_WHEN_read_THEN_pv_shows_disconnect(self):
        self._lewis.backdoor_set_on_device("pressure", None)
        # Setting none simulates no response from device which is like pulling the serial cable. Disconnecting the
        # emulator using the backdoor makes the record go udf not timeout which is what the actual device does.

        self.ca.assert_that_pv_alarm_is("PRESSURE", self.ca.Alarms.INVALID)

    @skip_if_recsim("Can not test disconnection in recsim")
    def test_GIVEN_device_not_connected_WHEN_get_pressure_THEN_alarm(self):
        self.ca.assert_that_pv_alarm_is("PRESSURE", ChannelAccess.Alarms.NONE, timeout=30)
        with self._lewis.backdoor_simulate_disconnected_device():
            self.ca.assert_that_pv_alarm_is("PRESSURE", ChannelAccess.Alarms.INVALID, timeout=30)
        # Assert alarms clear on reconnection
        self.ca.assert_that_pv_alarm_is("PRESSURE", ChannelAccess.Alarms.NONE, timeout=30)
