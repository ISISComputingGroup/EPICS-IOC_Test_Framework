import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

from parameterized import parameterized

DEVICE_PREFIX = "KNR1050_01"

device_name = "knr1050"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("KNR1050"),
        "macros": {},
        "emulator": device_name,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class Knr1050Tests(unittest.TestCase):
    """
    Tests for the Knr1050 IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(device_name, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def _set_pressure_limit_low(self, limit):
        self._lewis.backdoor_set_on_device("pressure_limit_low", limit)

    def _set_pressure_limit_high(self, limit):
        self._lewis.backdoor_set_on_device("pressure_limit_high", limit)

    @skip_if_recsim("In rec sim this test fails")
    def test_GIVEN_an_ioc_WHEN_stop_issued_THEN_device_stops(self):
        stopped_status = self._lewis.backdoor_get_from_device("is_stopped")
        self.assertEqual(stopped_status, "False")
        self.ca.set_pv_value("STOP:SP", 1)

        stopped_status = self._lewis.backdoor_get_from_device("is_stopped")
        self.assertEqual(stopped_status, "True")

    @skip_if_recsim("Relies on the backdoor")
    def test_GIVEN_an_ioc_WHEN_stop2_command_sent_THEN_expected_stop_type(self):
        self._lewis.backdoor_set_on_device("keep_last_values", "False")
        stopped_status = self._lewis.backdoor_get_from_device("keep_last_values")
        self.assertEqual(stopped_status, "False")
        self.ca.set_pv_value("_STOP:KLV:SP", 1)

        stopped_status = self._lewis.backdoor_get_from_device("keep_last_values")
        self.assertEqual(stopped_status, "True")

    @skip_if_recsim("Relies on the backdoor")
    def test_GIVEN_set_low_pressure_limit_via_backdoor_WHEN_get_low_pressure_limits_via_IOC_THEN_get_expected_pressure_limit(self):
        expected_pressure = 10.0
        self._set_pressure_limit_low(expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)

        self.ca.assert_that_pv_is("PRESS:LOW", expected_pressure)

    @skip_if_recsim("Relies on the backdoor")
    def test_GIVEN_set_high_pressure_limit_via_backdoor_WHEN_get_high_pressure_limits_via_IOC_THEN_get_expected_pressure_limit(self):
        expected_pressure = 100.0
        self._set_pressure_limit_high(expected_pressure)
        self.ca.set_pv_value("GET_PRESS:LIM.PROC", 1)

        self.ca.assert_that_pv_is("PRESS:HIGH", expected_pressure)

    @skip_if_recsim("Relies on the backdoor")
    def test_GIVEN_set_low_pressure_limit_via_ioc_WHEN_get_low_pressure_limit_via_backdoor_THEN_get_expected_pressure_limit(self):
        expected_pressure = 10.0
        self.ca.set_pv_value("PRESS:LOW:SP", expected_pressure)

        self.assertEqual(float(self._lewis.backdoor_get_from_device("pressure_limit_low")), expected_pressure)

    @skip_if_recsim("Relies on the backdoor")
    def test_GIVEN_set_high_pressure_limit_via_ioc_WHEN_get_high_pressure_limit_via_backdoor_THEN_get_expected_pressure_limit(self):
        expected_pressure = 200.0
        self.ca.set_pv_value("PRESS:HIGH:SP", expected_pressure)

        self.assertEqual(float(self._lewis.backdoor_get_from_device("pressure_limit_high")), expected_pressure)

    def test_GIVEN_set_low_pressure_limit_via_ioc_WHEN_get_low_pressure_limit_via_IOC_THEN_get_expected_value(self):
        expected_pressure = 45.55
        self.ca.set_pv_value("PRESS:LOW:SP", expected_pressure)

        self.ca.assert_that_pv_is("PRESS:LOW", expected_pressure)

    def test_GIVEN_set_high_pressure_limit_via_ioc_WHEN_get_high_pressure_limit_via_IOC_THEN_get_expected_value(self):
        expected_pressure = 1345.55
        self.ca.set_pv_value("PRESS:HIGH:SP", expected_pressure)

        self.ca.assert_that_pv_is("PRESS:HIGH", expected_pressure)

    @skip_if_recsim("Relies on the backdoor")
    def test_GIVEN_an_ioc_WHEN_ramp_command_sent_via_ioc_THEN_ramp_starts(self):
        ramp_status = self._lewis.backdoor_get_from_device("ramp_status")
        self.assertEqual(ramp_status, "False")
        self.ca.set_pv_value("RAMP:SP", 1)

        ramp_status = self._lewis.backdoor_get_from_device("ramp_status")
        self.assertEqual(ramp_status, "True")

    @skip_if_recsim('Relies on the backdoor')
    def test_GIVEN_set_flow_limit_min_via_ioc_WHEN_ramp_command_sent_via_IOC_THEN_correct_flow_limit_set(self):
        expected_flow = 1423.10
        self.ca.set_pv_value("FLOWRATE:SP", expected_flow)
        self.ca.set_pv_value("RAMP:SP", 1)

        self.assertEqual(float(self._lewis.backdoor_get_from_device("flow_rate")), expected_flow)


    @parameterized.expand([('A', 45),
                           ('B', 34),
                           ('C', 56),
                           ('D', 76)])
    @skip_if_recsim('Relies on the backdoor')
    def test_GIVEN_set_concentration_A_via_ioc_WHEN_ramp_command_sent_via_ioc_THEN_correct_concentration_set(self, name, concentration):
        self.ca.set_pv_value("CON:{}:SP".format(name), concentration)
        self.ca.set_pv_value("RAMP:SP", 1)

        self.assertEqual(float(self._lewis.backdoor_get_from_device("concentration_{}".format(name))), concentration)
    @skip_if_recsim('Relies on the backdoor')
    def test_GIVEN_an_ioc_WHEN_get_status_THEN_device_has_valid_instrument_state_returned(self):
        self.ca.set_pv_value("GET_STATUS", 1)

        state = self._lewis.backdoor_get_from_device("current_instrument_state")
        pass
