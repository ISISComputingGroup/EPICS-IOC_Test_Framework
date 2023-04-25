import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from parameterized.parameterized import parameterized

from utils.testing import get_running_lewis_and_ioc, unstable_test
# Device prefix
DEVICE_PREFIX = "SKFCHOPPER_01"

DEVICE_NAME = "skf_chopper"
OPEN = 127.8
CLOSED = 307.8
IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SKFCHOPPER"),
        "macros": {
            "NAME": "TEST_CHOPPER",
            "OPEN": OPEN,
            "CLOSED": CLOSED,
        },
        "emulator": DEVICE_NAME,
        "ioc_launcher_class": ProcServLauncher,
    },
]

TEST_MODES = [TestModes.DEVSIM]
PV_TO_WAIT_FOR = "FREQ"

class SkfG5ChopperTests(unittest.TestCase):
    """
    Tests for the SKF G5 Chopper Controller
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(DEVICE_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_correct_transaction_id_WHEN_not_skipping_THEN_state_correct(self):
        self._lewis.backdoor_set_on_device("send_ok_transid", True)
        expected = 56
        self._lewis.backdoor_set_on_device("freq", expected)
        self.ca.assert_that_pv_is("FREQ", expected, timeout=5)

    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_incorrect_transaction_id_WHEN_not_skipping_THEN_state_incorrect(self):
        self._lewis.backdoor_set_on_device("send_ok_transid", False)
        initial = self.ca.get_pv_value("FREQ")
        expected = 45
        self._lewis.backdoor_set_on_device("freq", expected)
        self.ca.assert_that_pv_is_not("FREQ", expected, timeout=5)
        self.ca.assert_that_pv_is("FREQ", initial, timeout=5)
    
    @parameterized.expand([True, False])
    @unstable_test(max_retries=5, wait_between_runs=10)
    def test_GIVEN_incorrect_transaction_id_WHEN_skipping_check_THEN_state_correct(self, send_correct_transaction_id):
        self._lewis.backdoor_set_on_device("send_ok_transid", send_correct_transaction_id)
        with self._ioc.start_with_macros({"SKIP_TRANSACTION_ID": 1, "NAME": "TEST_CHOPPER", "OPEN": OPEN, "CLOSED": CLOSED,}, pv_to_wait_for=PV_TO_WAIT_FOR):
            expected = 12
            self._lewis.backdoor_set_on_device("freq", expected)
            self.ca.assert_that_pv_is("FREQ", expected, timeout=5)

