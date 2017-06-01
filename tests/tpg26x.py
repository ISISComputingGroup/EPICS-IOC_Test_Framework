import unittest

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc

# MACROS to use for the IOC
MACROS = {}


class Tpg26xTests(unittest.TestCase):
    """
    Tests for the TPG26x
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("TPG26x")

        self.ca = ChannelAccess()
        self.ca.wait_for("TPG26X_01:1:PRESSURE")

    def _set_pressure(self, expected_pressure):
        self._lewis.backdoor_set_on_device("pressure", expected_pressure)
        self._ioc.set_simulated_value("TPG26X_01:SIM:1:PRESSURE", expected_pressure)

    def test_GIVEN_pressure_set_WHEN_read_THEN_pressure_is_as_expected(self):
        expected_pressure = 1.23
        self._set_pressure(expected_pressure)

        self.ca.assert_that_pv_is("TPG26X_01:1:PRESSURE", expected_pressure)
        self.ca.assert_pv_alarm_is("TPG26X_01:1:PRESSURE", ChannelAccess.ALARM_NONE)
        self.ca.assert_that_pv_is("TPG26X_01:1:ERROR", "No Error")

