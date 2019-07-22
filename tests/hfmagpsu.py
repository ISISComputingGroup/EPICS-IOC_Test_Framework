import unittest
from utils.channel_access import ChannelAccess
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir
import time

DEVICE_PREFIX = "HFMAGPSU_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HFMAGPSU"),
        "macros": {},
        "emulator": "HFMAGPSU"
    },
]


class EnumValues(object):
    AMPS = 0
    TESLA = 1
    ON = 1
    OFF = 0


class StringValues(object):
    TESLA = "TESLA"
    AMPS = "AMPS"
    ON = "ON"
    OFF = "OFF"


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class HfmagpsuTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("HFMAGPSU", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
        self.ca.assert_that_pv_exists("DIRECTION")
        time.sleep(8)

    def test_GIVEN_midTarget_set_WHEN_read_THEN_midTarget_is_as_expected(self):
        test_value = 2.325
        self.ca.assert_setting_setpoint_sets_readback(test_value, "MID")

    def test_GIVEN_rampRate_set_WHEN_read_THEN_rampRate_is_as_expected(self):
        test_value = 0.51
        self.ca.assert_setting_setpoint_sets_readback(test_value, "RAMPRATE")

    def test_GIVEN_maxTarget_set_WHEN_read_THEN_maxTarget_is_as_expected(self):
        test_value = 4.0
        self.ca.assert_setting_setpoint_sets_readback(test_value, "MAX")

    def test_GIVEN_limit_set_WHEN_read_THEN_limit_is_as_expected(self):
        test_value = 35.5
        self.ca.assert_setting_setpoint_sets_readback(test_value, "LIMIT")

    def test_GIVEN_constant_set_WHEN_read_THEN_constant_is_as_expected(self):
        test_value = 0.0032
        self.ca.assert_setting_setpoint_sets_readback(test_value, "CONSTANT")

    def test_GIVEN_heaterValue_set_WHEN_read_THEN_heaterValue_is_as_expected(self):
        test_value = 15.5
        self.ca.assert_setting_setpoint_sets_readback(test_value, "HEATERVALUE")

    def test_GIVEN_pause_set_ON_WHEN_read_THEN_pause_is_as_expected(self):
        expected_output = StringValues.ON
        set_value = EnumValues.ON
        self.ca.assert_setting_setpoint_sets_readback(set_value, "PAUSE", "PAUSE:SP", expected_output)

    def test_GIVEN_pause_set_OFF_WHEN_read_THEN_pause_is_as_expected(self):
        expected_output = StringValues.OFF
        set_value = EnumValues.OFF
        self.ca.assert_setting_setpoint_sets_readback(set_value, "PAUSE", "PAUSE:SP", expected_output)

    def test_GIVEN_outputMode_set_TESLA_WHEN_read_THEN_outputMode_is_as_expected(self):
        expected_output = StringValues.TESLA
        set_value = EnumValues.TESLA
        self.ca.assert_setting_setpoint_sets_readback(set_value, "OUTPUTMODE", "OUTPUTMODE:SP", expected_output)

    def test_GIVEN_heaterStatus_set_ON_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_output = StringValues.ON
        set_value = EnumValues.ON
        self.ca.assert_setting_setpoint_sets_readback(set_value, "HEATERSTATUS", "HEATERSTATUS:SP", expected_output)

    def test_GIVEN_heaterStatus_set_OFF_WHEN_read_THEN_heaterStatus_is_as_expected(self):
        expected_output = StringValues.OFF
        set_value = EnumValues.OFF
        self.ca.assert_setting_setpoint_sets_readback(set_value, "HEATERSTATUS", "HEATERSTATUS:SP", expected_output)

    def test_GIVEN_rampTarget_set_WHEN_read_THEN_rampTarget_is_as_expected(self):
        ramp_targets = ['ZERO', 'MID', 'MAX']
        for index, expected_output in enumerate(ramp_targets):
            self.ca.assert_setting_setpoint_sets_readback(index, "RAMPTARGET", "RAMPTARGET:SP", expected_output)

    def test_GIVEN_direction_set_WHEN_read_THEN_direction_is_as_expected(self):
        directions = ["0", "-", "+"]
        for index, expected_output in enumerate(directions):
            self.ca.assert_setting_setpoint_sets_readback(index, "DIRECTION", "DIRECTION:SP", expected_output)
