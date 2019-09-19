import unittest

from parameterized import parameterized

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir

from utils.ioc_launcher import IOCRegister, IocLauncher
from utils.testing import get_running_lewis_and_ioc, parameterized_list

DEVICE_PREFIX = "CP2800_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CP2800"),
        "macros": {},
    },
]

TEST_MODES = [TestModes.RECSIM]


class CP2800StatusTests(unittest.TestCase):

    def setUp(self):
        _, self._ioc = get_running_lewis_and_ioc(None, DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_GIVEN_compressor_elapsed_minutes_THEN_alarm_correct(self):
        tests = [(-1, self.ca.Alarms.MAJOR),
                 (0, self.ca.Alarms.NONE),
                 (1, self.ca.Alarms.NONE),
                 (500001, self.ca.Alarms.MINOR),
                 (1000001, self.ca.Alarms.MAJOR),
                 ]
        for test in tests:
            elapsed_time, expected_alarm = test
            self.ca.set_pv_value("SIM:ELAPSED", elapsed_time)
            self.ca.assert_that_pv_alarm_is("ELAPSED", expected_alarm, 10)

    def test_GIVEN_compressor_state_on_or_off_THEN_readback_correct(self):
        states = [(1, "On"), (0, "Off")]
        for state in states:
            send_val, expected_response = state
            self.ca.set_pv_value("SIM:POWER", send_val)
            self.ca.assert_that_pv_is("POWER", expected_response)

    def test_GIVEN_error_value_THEN_readback_correct(self):
        self.ca.set_pv_value("SIM:ERR", 1)
        self.ca.assert_that_pv_is("ERR", 1, timeout=10)

    def test_GIVEN_negative_error_value_THEN_alarm_correct(self):
        self.ca.set_pv_value("SIM:ERR", -1)
        self.ca.assert_that_pv_alarm_is("ERR", self.ca.Alarms.MAJOR, timeout=10)
