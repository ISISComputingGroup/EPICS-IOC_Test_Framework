import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list, skip_if_recsim

DEVICE_PREFIX = "LKSH372_01"
_EMULATOR_NAME = "lakeshore372"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LKSH372"),
        "emulator": _EMULATOR_NAME,
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

TEST_TEMPERATURES = [0, 0.001, 321.123]
HEATER_RANGES = [
    "Off",
    "31.6 uA",
    "100 uA",
    "316 uA",
    "1 mA",
    "3.16 mA",
    "10 mA",
    "31.6 mA",
    "100 mA",
]

TEST_HEATER_POWER_PERCENTAGES = [0, 0.01, 99.99]
TEST_SENSOR_RESISTANCES = [0, 0.000005, 23.456]

# P is floating-point, I and D are integers
TEST_PID_PARAMS = [
    (0.0, 0, 0),
    (0.01, 1, 1),
    (12.34, 567, 890),
]


class Lakeshore372Tests(unittest.TestCase):
    """
    Tests for the lakeshore 372 IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(_EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=15)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def _assert_readback_alarm_states(self, alarm):
        for readback_pv in [
            "TEMP",
            "TEMP:SP:RBV",
            "P",
            "I",
            "D",
            "HEATER:POWER",
            "RESISTANCE",
            "HEATER:RANGE",
        ]:
            self.ca.assert_that_pv_alarm_is(readback_pv, alarm)

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_WHEN_temp_setpoint_is_set_THEN_actual_temperature_updates(self, _, temperature):
        self.ca.assert_setting_setpoint_sets_readback(
            temperature, set_point_pv="TEMP:SP", readback_pv="TEMP"
        )

    @parameterized.expand(parameterized_list(TEST_TEMPERATURES))
    def test_WHEN_temp_setpoint_is_set_THEN_setpoint_readback_updates(self, _, temperature):
        self.ca.assert_setting_setpoint_sets_readback(
            temperature, set_point_pv="TEMP:SP", readback_pv="TEMP:SP:RBV"
        )

    @parameterized.expand(parameterized_list(HEATER_RANGES))
    def test_WHEN_heater_range_is_set_THEN_heater_range_readback_updates(self, _, rng):
        self.ca.assert_setting_setpoint_sets_readback(
            rng, set_point_pv="HEATER:RANGE:SP", readback_pv="HEATER:RANGE"
        )

    @parameterized.expand(parameterized_list(TEST_HEATER_POWER_PERCENTAGES))
    @skip_if_recsim("Uses lewis backdoor")
    def test_WHEN_heater_power_is_set_via_backdoor_THEN_heater_power_pv_updates(self, _, pwr):
        self._lewis.backdoor_set_on_device("heater_power", pwr)
        self.ca.assert_that_pv_is_number("HEATER:POWER", pwr, tolerance=0.001)

    @parameterized.expand(parameterized_list(TEST_SENSOR_RESISTANCES))
    @skip_if_recsim("Uses lewis backdoor")
    def test_WHEN_sensor_resistance_is_set_via_backdoor_THEN_resistance_pv_updates(self, _, res):
        self._lewis.backdoor_set_on_device("sensor_resistance", res)
        self.ca.assert_that_pv_is_number("RESISTANCE", res, tolerance=0.000001)

    @parameterized.expand(parameterized_list(TEST_PID_PARAMS))
    def test_WHEN_pid_parameters_are_set_THEN_readbacks_update(self, _, p, i, d):
        # Simulate a script by writing PIDs all in one go without waiting for update first.
        self.ca.set_pv_value("P:SP", p)
        self.ca.set_pv_value("I:SP", i)
        self.ca.set_pv_value("D:SP", d)
        self.ca.assert_that_pv_is("P", p)
        self.ca.assert_that_pv_is("I", i)
        self.ca.assert_that_pv_is("D", d)

    @skip_if_recsim("Recsim does not support simulated disconnection")
    def test_WHEN_device_does_not_respond_THEN_pvs_go_into_invalid_alarm(self):
        self._assert_readback_alarm_states(self.ca.Alarms.NONE)
        with self._lewis.backdoor_simulate_disconnected_device():
            self._assert_readback_alarm_states(self.ca.Alarms.INVALID)
        # Assert alarms clear on reconnection
        self._assert_readback_alarm_states(self.ca.Alarms.NONE)

    @skip_if_recsim("Complex logic not testable in recsim")
    def test_WHEN_temperature_setpoint_is_sent_THEN_control_mode_changed_to_5(self):
        # 5 is the control mode for closed loop PID control, which should always be sent along with a temperature set.
        self._lewis.backdoor_set_on_device("control_mode", 0)
        self._lewis.assert_that_emulator_value_is("control_mode", 0, cast=int)
        self.ca.set_pv_value("TEMP:SP", 0)
        self._lewis.assert_that_emulator_value_is("control_mode", 5, cast=int)
