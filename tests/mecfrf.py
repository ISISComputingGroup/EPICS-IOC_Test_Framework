from __future__ import division, absolute_import, unicode_literals, print_function

import itertools
import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list, skip_if_devsim

DEVICE_PREFIX = "MECFRF_01"
_EMULATOR_NAME = "mecfrf"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("MECFRF"),
        "emulator": _EMULATOR_NAME,
    },
]


TEST_MODES = [
    TestModes.RECSIM,
    TestModes.DEVSIM,
]

TEST_LENGTHS = [1234.5678, 1, 0]
SENSORS = (1, 2)

RAW_READING_SCALING = 1000000


class MecfrfTests(unittest.TestCase):

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(_EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)

        self._lewis.backdoor_set_on_device("connected", True)
        self._lewis.backdoor_set_on_device("corrupted_messages", False)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    @parameterized.expand(parameterized_list(itertools.product(SENSORS, TEST_LENGTHS)))
    @skip_if_recsim("Uses Lewis backdoor")
    def test_WHEN_value_is_written_to_emulator_THEN_record_updates(self, _, sensor, length):
        self._lewis.backdoor_set_on_device("sensor{}".format(sensor), length * RAW_READING_SCALING)
        self.ca.assert_that_pv_is("SENSOR{}".format(sensor), length)
        self.ca.assert_that_pv_alarm_is("SENSOR{}".format(sensor), self.ca.Alarms.NONE)

    @skip_if_recsim("Uses Lewis backdoor")
    def test_WHEN_emulator_sends_corrupt_packets_THEN_records_go_into_alarm(self):
        with self.ca.assert_pv_processed("_RESET_CONNECTION"):
            self._lewis.backdoor_set_on_device("corrupted_messages", True)
            self.ca.assert_that_pv_is("_GETTING_INVALID_MESSAGES", 1)

        self._lewis.backdoor_set_on_device("corrupted_messages", False)
        self.ca.assert_that_pv_is("_GETTING_INVALID_MESSAGES", 0)

    @parameterized.expand(parameterized_list(SENSORS))
    @skip_if_recsim("Uses Lewis backdoor")
    def test_WHEN_emulator_disconnected_THEN_records_go_into_alarm(self, _, sensor):
        self.ca.assert_that_pv_is("_READINGS_OUTDATED", "No")
        self.ca.assert_that_pv_alarm_is("SENSOR{}".format(sensor), self.ca.Alarms.NONE)

        self._lewis.backdoor_set_on_device("connected", False)

        self.ca.assert_that_pv_is("_READINGS_OUTDATED", "Yes")
        self.ca.assert_that_pv_alarm_is("SENSOR{}".format(sensor), self.ca.Alarms.INVALID)
