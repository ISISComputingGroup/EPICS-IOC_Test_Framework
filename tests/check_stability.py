import operator
import unittest
import os

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.test_modes import TestModes
from utils.testing import parameterized_list

DEVICE_PREFIX = "UTILITIESTEST"

EPICS_ROOT = os.getenv("EPICS_KIT_ROOT")

TOLERANCE = 0.1
NUMBER_OF_SAMPLES = 5

IOCS = [
    {
        "pv_for_existence": "VAL",
        "name": DEVICE_PREFIX,
        "directory": os.path.realpath(
            os.path.join(EPICS_ROOT, "support", "utilities", "master", "iocBoot", "iocutilitiesTest")),
        "macros": {
            "TOLERANCE": TOLERANCE,
            "NSAMP": NUMBER_OF_SAMPLES,
        }
    },
]

TEST_MODES = [TestModes.RECSIM]


class SimpleTests(unittest.TestCase):
    """
    Tests for the stability checking logic
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.assertIsNotNone(self._ioc)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=3)

        self.ca.assert_that_pv_exists("VAL")
        self.ca.assert_that_pv_exists("VAL:SP")

        self.ca.assert_that_pv_is_number("STAB:IS_STABLE.E", TOLERANCE)

        # Need to do this to ensure buffer is properly up before starting any tests
        self.ca.assert_that_pv_exists("STAB:_VAL_BUFF")
        while int(self.ca.get_pv_value("STAB:_VAL_BUFF.NUSE")) < NUMBER_OF_SAMPLES:
            self.ca.process_pv("VAL")

    def test_GIVEN_pv_not_changing_and_WHEN_pv_exactly_equal_to_sp_THEN_stable(self):
        test_value = 100
        self.ca.set_pv_value("VAL:SP", test_value)
        for _ in range(NUMBER_OF_SAMPLES):
            self.ca.set_pv_value("VAL", test_value)

        self.ca.assert_that_pv_is("STAB:HAS_RECENT_ALARM", False)
        self.ca.assert_that_pv_is("STAB:IS_STABLE", True)

    @parameterized.expand(parameterized_list([operator.add, operator.sub]))
    def test_GIVEN_pv_not_changing_and_WHEN_pv_outside_tolerance_of_sp_THEN_stable(self, _, op):
        test_value = 200
        self.ca.set_pv_value("VAL:SP", test_value)
        for _ in range(NUMBER_OF_SAMPLES):
            self.ca.set_pv_value("VAL", op(test_value, 1.1 * TOLERANCE))

        self.ca.assert_that_pv_is("STAB:HAS_RECENT_ALARM", False)
        self.ca.assert_that_pv_is("STAB:IS_STABLE", False)

    @parameterized.expand(parameterized_list([operator.add, operator.sub]))
    def test_GIVEN_pv_not_changing_and_WHEN_pv_inside_tolerance_of_sp_THEN_stable(self, _, op):
        test_value = 300
        self.ca.set_pv_value("VAL:SP", test_value)
        for _ in range(NUMBER_OF_SAMPLES):
            self.ca.set_pv_value("VAL", op(test_value, 0.9 * TOLERANCE))

        self.ca.assert_that_pv_is("STAB:HAS_RECENT_ALARM", False)
        self.ca.assert_that_pv_is("STAB:IS_STABLE", True)

    def test_GIVEN_one_out_of_range_value_at_end_of_buffer_THEN_unstable(self):
        stable_value = 400
        self.ca.set_pv_value("VAL:SP", stable_value)
        for _ in range(NUMBER_OF_SAMPLES - 1):
            self.ca.set_pv_value("VAL", stable_value)
        self.ca.set_pv_value("VAL", stable_value + 1.1 * TOLERANCE)

        self.ca.assert_that_pv_is("STAB:HAS_RECENT_ALARM", False)
        self.ca.assert_that_pv_is("STAB:IS_STABLE", False)

    def test_GIVEN_one_out_of_range_value_at_beginning_of_buffer_THEN_unstable(self):
        stable_value = 500
        self.ca.set_pv_value("VAL:SP", stable_value)
        self.ca.set_pv_value("VAL", stable_value + 1.1 * TOLERANCE)

        for _ in range(NUMBER_OF_SAMPLES - 1):
            self.ca.set_pv_value("VAL", stable_value)

        self.ca.assert_that_pv_is("STAB:HAS_RECENT_ALARM", False)
        self.ca.assert_that_pv_is("STAB:IS_STABLE", False)
