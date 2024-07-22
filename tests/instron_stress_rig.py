import unittest

from common_tests.instron_base import InstronBase
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.build_architectures import BuildArchitectures

# Device prefix
from utils.testing import skip_if_recsim

DEVICE_PREFIX = "INSTRON_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("INSTRON"),
        "macros": {},
        "emulator": "instron_stress_rig",
    },
]

TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
# VISA not yet available on 32 bit
BUILD_ARCHITECTURES = [BuildArchitectures._64BIT]


class InstronTests(InstronBase, unittest.TestCase):
    def get_prefix(self):
        return DEVICE_PREFIX

    def _switch_to_position_channel_and_change_setpoint(self):
        # It has to be big or the set point will be reached before the test completes
        _big_set_point = 999999999999

        # Select position as control channel
        self._change_channel("Position")
        # Change the setpoint so that movement can be started
        self.ca.set_pv_value("POS:SP", _big_set_point)
        self.ca.assert_that_pv_is_number("POS:SP", _big_set_point, tolerance=1)
        self.ca.assert_that_pv_is_number("POS:SP:RBV", _big_set_point, tolerance=1)

    @skip_if_recsim("Dynamic behaviour not captured in RECSIM")
    def test_WHEN_going_and_then_stopping_THEN_going_pv_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("GOING", "NO")
        self._switch_to_position_channel_and_change_setpoint()
        self.ca.set_pv_value("MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("GOING", "YES")
        self.ca.set_pv_value("STOP:SP", 1)
        self.ca.assert_that_pv_is("GOING", "NO")
        self.ca.set_pv_value("STOP:SP", 0)

    @skip_if_recsim("Dynamic behaviour not captured in RECSIM")
    def test_WHEN_going_and_then_panic_stopping_THEN_going_pv_reflects_the_expected_state(self):
        self.ca.assert_that_pv_is("GOING", "NO")
        self._switch_to_position_channel_and_change_setpoint()
        self.ca.set_pv_value("MOVE:GO:SP", 1)
        self.ca.assert_that_pv_is("GOING", "YES")
        self.ca.set_pv_value("PANIC:SP", 1)
        self.ca.assert_that_pv_is("GOING", "NO")
        self.ca.set_pv_value("PANIC:SP", 0)

    @skip_if_recsim("In rec sim this test fails")
    def test_WHEN_arbitrary_command_C4_is_sent_THEN_Q4_gives_back_the_value_that_was_just_set(self):
        def _set_and_check(value):
            # Put the record into a non-alarm state. This is needed so that we can wait until the record is in alarm
            # later, when we do a command which (expectedly) puts the record into a timeout alarm.
            self.ca.set_pv_value("ARBITRARY:SP", "Q4,1", sleep_after_set=1.0)
            self.ca.assert_that_pv_alarm_is("ARBITRARY", self.ca.Alarms.NONE)

            self.ca.set_pv_value("ARBITRARY:SP", "C4,1," + str(value), sleep_after_set=1.0)
            self.ca.assert_that_pv_is("ARBITRARY:SP", "C4,1," + str(value))

            self.ca.set_pv_value("ARBITRARY:SP", "Q4,1", sleep_after_set=1.0)
            self.ca.assert_that_pv_is_number("ARBITRARY", value, tolerance=0.001, timeout=10)

        for v in [0, 1, 0]:
            _set_and_check(v)
