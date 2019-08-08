import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "MKSPR4KB_01"
EMULATOR_NAME = "mkspr4kb"

HE3POT_COARSE_TIME = 20
DRIFT_BUFFER_SIZE = 20

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MKSPR4KB"),
        "emulator": EMULATOR_NAME,
    },
]


TEST_MODES = [
    TestModes.DEVSIM,
    TestModes.RECSIM,
]

TEST_FLOAT_VALUES = (-12.34, 0, 1, 99.99)
TEST_INTEGER_VALUES = (-5, 0, 123)
VALVE_STATES = ["ON", "OFF"]
RELAY_STATES = ["ON", "OFF"]
SIGNAL_MODES = ["METER", "OFF", "INDEP", "EXTRN", "SLAVE", "RTD"]
LIMIT_MODES = ["SLEEP", "LIMIT", "BAND", "MLIMIT", "MBAND", "RTD"]
CONTROL_MODES = ["LOCAL", "REMOTE"]
UNITS = ["uBar", "mBar", "Bar", "mTor", "Torr", "kTor", "Pa", "kPa", "mH2O", "cH2O", "PSI", "N/qm", "SCCM", "SLM",
         "SCM", "SCFH", "SCFM", "mA", "V", "%", "C"]


CHANNELS = ["CH1", "CH2"]


class MKS_PR4000B_Tests(unittest.TestCase):
    """
    Tests for the MKSPR4K IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

    def test_WHEN_ioc_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(CHANNELS))
    def test_WHEN_ioc_is_started_THEN_channels_are_not_disabled(self, _, chan):
        self.ca.assert_that_pv_is("{}:DISABLE".format(chan), "COMMS ENABLED")

    @parameterized.expand(parameterized_list(CONTROL_MODES))
    def test_WHEN_set_control_mode_THEN_readback_updates(self, _, mode):
        self.ca.assert_setting_setpoint_sets_readback(
            mode, "REMOTEMODE", expected_alarm=self.ca.Alarms.MAJOR if mode == "LOCAL" else self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_FLOAT_VALUES)))
    def test_WHEN_channel_setpoint_is_set_THEN_setpoint_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:VAL:SP".format(chan), readback_pv="{}:VAL:SP:RBV".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_FLOAT_VALUES)))
    def test_WHEN_channel_setpoint_is_set_THEN_value_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:VAL:SP".format(chan), readback_pv="{}:VAL".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, VALVE_STATES)))
    def test_WHEN_valve_state_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:VALVE:SP".format(chan), readback_pv="{}:VALVE".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, VALVE_STATES)))
    def test_WHEN_relay_state_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:RELAY:SP".format(chan), readback_pv="{}:RELAY".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_FLOAT_VALUES)))
    def test_WHEN_gain_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:GAIN:SP".format(chan), readback_pv="{}:GAIN".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_INTEGER_VALUES)))
    def test_WHEN_offset_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:OFFSET:SP".format(chan), readback_pv="{}:OFFSET".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_INTEGER_VALUES)))
    def test_WHEN_rtd_offset_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:RTDOFFSET:SP".format(chan), readback_pv="{}:RTDOFFSET".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_INTEGER_VALUES)))
    def test_WHEN_input_range_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:INP:RANGE:SP".format(chan), readback_pv="{}:INP:RANGE".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_INTEGER_VALUES)))
    def test_WHEN_output_range_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:OUTP:RANGE:SP".format(chan), readback_pv="{}:OUTP:RANGE".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_INTEGER_VALUES)))
    def test_WHEN_external_input_range_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:EXTINP:RANGE:SP".format(chan), readback_pv="{}:EXTINP:RANGE".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_INTEGER_VALUES)))
    def test_WHEN_external_output_range_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:EXTOUTP:RANGE:SP".format(chan), readback_pv="{}:EXTOUTP:RANGE".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, SIGNAL_MODES)))
    def test_WHEN_signal_mode_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:SIGNALMODE:SP".format(chan), readback_pv="{}:SIGNALMODE".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, LIMIT_MODES)))
    def test_WHEN_limit_mode_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:LIMITMODE:SP".format(chan), readback_pv="{}:LIMITMODE".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_FLOAT_VALUES)))
    def test_WHEN_upper_limit_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:UPPERLIMIT:SP".format(chan), readback_pv="{}:UPPERLIMIT".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_FLOAT_VALUES)))
    def test_WHEN_lower_limit_setpoint_is_set_THEN_readback_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, set_point_pv="{}:LOWERLIMIT:SP".format(chan), readback_pv="{}:LOWERLIMIT".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_FLOAT_VALUES)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_external_input_is_set_via_backdoor_THEN_readback_updates(self, _, chan, val):
        assert chan.startswith("CH")
        chan_number = chan[len("CH"):]
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [chan_number, "external_input", val])
        self.ca.assert_that_pv_is_number("{}:EXTIN".format(chan), val, tolerance=0.001)

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, UNITS)))
    @skip_if_recsim("Complex behaviour not properly emulated (values push from protocol).")
    def test_WHEN_range_units_are_set_THEN_readbacks_updates(self, _, chan, units):
        self.ca.assert_setting_setpoint_sets_readback(
            units, readback_pv="{}:RANGE:UNITS".format(chan), set_point_pv="{}:RANGE:UNITS:SP".format(chan))

    @parameterized.expand(parameterized_list(itertools.product(CHANNELS, TEST_FLOAT_VALUES)))
    @skip_if_recsim("Complex behaviour not properly emulated (values push from protocol).")
    def test_WHEN_range_is_set_THEN_readbacks_updates(self, _, chan, val):
        self.ca.assert_setting_setpoint_sets_readback(
            val, readback_pv="{}:RANGE".format(chan), set_point_pv="{}:RANGE:SP".format(chan))
