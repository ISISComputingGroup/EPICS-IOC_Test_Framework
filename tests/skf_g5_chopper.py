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
        self._lewis.backdoor_set_on_device("send_ok_transid", True)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    # sending invalid transaction ids can cause lots of ioc timeouts and can cause a big buildup
    # of pending reads in the ioc if it is expecting valid ones. So make sure we reset emulator to 
    # an OK state at end of test so when ioc restarts for next test it doesn't get stuck
    def tearDown(self):
        self._lewis.backdoor_set_on_device("send_ok_transid", True)

    def test_GIVEN_correct_transaction_id_WHEN_not_skipping_THEN_state_correct(self):
        self._lewis.backdoor_set_on_device("send_ok_transid", True)
        expected = 56
        self._lewis.backdoor_set_on_device("freq", expected)
        self.ca.assert_that_pv_is("FREQ", expected, timeout=15)

    def test_GIVEN_incorrect_transaction_id_WHEN_not_skipping_THEN_state_incorrect(self):
        self._lewis.backdoor_set_on_device("send_ok_transid", False)
        initial = self.ca.get_pv_value("FREQ")
        expected = 45
        self._lewis.backdoor_set_on_device("freq", expected)
        self.ca.assert_that_pv_is_not("FREQ", expected, timeout=5)
        self.ca.assert_that_pv_is("FREQ", initial, timeout=5)
    
    @parameterized.expand([True, False])
    def test_GIVEN_incorrect_transaction_id_WHEN_skipping_check_THEN_state_correct(self, send_correct_transaction_id):
        self._lewis.backdoor_set_on_device("send_ok_transid", send_correct_transaction_id)
        with self._ioc.start_with_macros({"SKIP_TRANSACTION_ID": 1, "NAME": "TEST_CHOPPER", "OPEN": OPEN, "CLOSED": CLOSED,}, pv_to_wait_for=PV_TO_WAIT_FOR):
            expected = 12
            self.ca.assert_that_pv_is_not("FREQ", expected, timeout=5)
            self._lewis.backdoor_set_on_device("freq", expected)
            self.ca.assert_that_pv_is("FREQ", expected, timeout=30)
            self._lewis.backdoor_set_on_device("freq", expected + 1) # so not remembered in emulator for next test

    @parameterized.expand(["V13", "W13", "V24", "W24", "Z12"])
    def test_GIVEN_normalised_and_fsv_value_WHEN_peak_position_read_THEN_position_correct(self, pos):
        norm = 10000
        fsv = 1234
        # Calculate peak position in engineering units.
        expected = ((norm + 32767) / 65534) * (2 * fsv) - fsv

        self._lewis.backdoor_set_on_device(f"{pos.lower()}_norm", norm)
        self._lewis.backdoor_set_on_device(f"{pos.lower()}_fsv", fsv)
        
        self.ca.assert_that_pv_is(f"{pos}:NORM", norm, timeout=90)
        self.ca.assert_that_pv_is(f"{pos}:FSV", fsv, timeout=90)
        self.ca.assert_that_pv_is(pos, expected)
