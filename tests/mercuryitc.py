import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, EPICS_TOP
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list
import os


DEVICE_PREFIX = "MERCURY_01"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": os.path.join(EPICS_TOP, "ioc", "master", "MERCURY_ITC", "iocBoot", "iocMERCURY-IOC-01"),
        "emulator": "mercuryitc",
        "macros": {
            "VI_TEMP_1": "1"
        }
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


PID_PARAMS = ["P", "I", "D"]
PID_TEST_VALUES = [0.0, 0.01, 99.99]
TEMPERATURE_TEST_VALUES = [0.0, 0.01, 999.9999]

PRIMARY_TEMPERATURE_CHANNEL = "MB0"


class MercuryTests(unittest.TestCase):
    """
    Tests for the Mercury IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("mercuryitc", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(itertools.product(PID_PARAMS, PID_TEST_VALUES)))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_pid_params_set_via_backdoor_THEN_pv_updates(self, _, param, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [PRIMARY_TEMPERATURE_CHANNEL, param.lower(), test_value])
        self.ca.assert_that_pv_is("1:{}".format(param), test_value)

    @parameterized.expand(parameterized_list(TEMPERATURE_TEST_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_actual_temp_is_set_via_backdoor_THEN_pv_updates(self, _, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [PRIMARY_TEMPERATURE_CHANNEL, "temperature", test_value])
        self.ca.assert_that_pv_is("1:TEMP", test_value)

    @parameterized.expand(parameterized_list(TEMPERATURE_TEST_VALUES))
    @skip_if_recsim("Lewis backdoor not available in recsim")
    def test_WHEN_sp_temp_is_set_via_backdoor_THEN_pv_updates(self, _, test_value):
        self._lewis.backdoor_run_function_on_device(
            "backdoor_set_channel_property", [PRIMARY_TEMPERATURE_CHANNEL, "temperature_sp", test_value])
        self.ca.assert_that_pv_is("1:TEMP:SP:RBV", test_value)
