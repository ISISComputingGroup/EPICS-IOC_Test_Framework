import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import parameterized_list
import os
from genie_python import genie as g
from parameterized import parameterized


IOC_PREFIX = "TIZR_01"
DEVICE_PREFIX = g.my_pv_prefix
SIMPLE_VALUE_ONE = "SIMPLE:VALUE1:SP"
SIMPLE_VALUE_TWO = "SIMPLE:VALUE2"

# Values chosen to be within high range of simple PVs
PVONE_MAX = 12
PVTWO_MAX = 8
SAFE_VALUE = 11


IOCS = [
    {
        "name": IOC_PREFIX,
        "directory": get_default_ioc_dir("TIZR"),
        "macros": {
            "PVONE": "{prefix}{pv}".format(prefix=DEVICE_PREFIX, pv=SIMPLE_VALUE_ONE),
            "PVTWO": "{prefix}{pv}".format(prefix=DEVICE_PREFIX, pv=SIMPLE_VALUE_TWO),
            "PVONE_MAX": PVONE_MAX,
            "PVTWO_MAX": PVTWO_MAX,
            "SAFE_VALUE": SAFE_VALUE
        },
    },
    {
        "name": "SIMPLE",
        "directory": os.path.join(EPICS_TOP, "ISIS", "SimpleIoc", "master", "iocBoot", "iocsimple"),
        "macros": {},
    }
]

WARNING_PV = "{}:TIZRWARNING".format(IOC_PREFIX)

TEST_MODES = [TestModes.RECSIM]


class TiZrTests(unittest.TestCase):
    """
    Tests for the TiZr cell monitoring logic.
    """

    def setUp(self):
        self._ioc = IOCRegister.get_running(IOC_PREFIX)
        self.ca = ChannelAccess(default_timeout=20)

        for pv in [SIMPLE_VALUE_ONE, SIMPLE_VALUE_TWO]:
            self.ca.assert_that_pv_exists(pv)

        self.set_safe_values()

    def set_safe_values(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 0.5*PVONE_MAX)
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 0.5*PVTWO_MAX)
        self.ca.set_pv_value(WARNING_PV, 0)

    def test_GIVEN_PVONE_above_max_WHEN_PVTWO_goes_out_of_range_THEN_alarm_and_safe_value_written_to_PVONE(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 2.0*PVONE_MAX)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, 2.0*PVONE_MAX, tolerance=1e-4)

        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 2.0*PVTWO_MAX)

        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)

        self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.MAJOR)

    def test_GIVEN_PVTWO_above_max_WHEN_PVONE_out_of_range_THEN_alarm_and_safe_value_written_to_PVONE(self):
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 2.0*PVTWO_MAX)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, 2.0*PVTWO_MAX, tolerance=1e-4)

        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 2.0*PVONE_MAX)

        self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.MAJOR)

        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, SAFE_VALUE, tolerance=1e-4)

    def test_GIVEN_PVONE_and_PVTWO_in_range_WHEN_in_range_value_written_THEN_no_alarm_and_value_written(self):
        self.ca.set_pv_value(SIMPLE_VALUE_ONE, 0.5*PVONE_MAX)
        self.ca.set_pv_value(SIMPLE_VALUE_TWO, 0.5*PVTWO_MAX)

        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_ONE, 0.5*PVONE_MAX)
        self.ca.assert_that_pv_is_number(SIMPLE_VALUE_TWO, 0.5*PVTWO_MAX)

        self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.NONE)

        self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_ONE, self.ca.Alarms.NONE)
        self.ca.assert_that_pv_alarm_is(SIMPLE_VALUE_TWO, self.ca.Alarms.NONE)

    @parameterized.expand(parameterized_list([(SIMPLE_VALUE_ONE, 0.5*PVONE_MAX), (SIMPLE_VALUE_TWO, 0.5*PVTWO_MAX)]))
    def test_GIVEN_PVONE_and_PVTWO_in_range_WHEN_out_of_range_value_written_to_one_THEN_no_alarm_and_value_written(
            self, _, pv, in_range_value):
        self.ca.set_pv_value(pv, in_range_value)
        self.ca.assert_that_pv_is_number(pv, in_range_value)
        self.ca.assert_that_pv_alarm_is(WARNING_PV, self.ca.Alarms.NONE)
        self.ca.assert_that_pv_alarm_is(pv, self.ca.Alarms.NONE)
