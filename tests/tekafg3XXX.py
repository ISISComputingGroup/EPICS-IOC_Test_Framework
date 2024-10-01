import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "TEKAFG3XXX_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("TEKAFG3XXX"),
        "macros": {"SCAN": "Passive"},
        "emulator": "tekafg3XXX",
    },
]


TEST_MODES = [TestModes.DEVSIM]


class Tekafg3XXXTests(unittest.TestCase):
    """
    Tests for the Afg3021B IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("tekafg3XXX", DEVICE_PREFIX)
        self.ca = ChannelAccess(
            device_prefix=DEVICE_PREFIX, default_wait_time=0.0, default_timeout=10
        )
        self._lewis.backdoor_set_on_device("connected", True)

    def test_GIVEN_nothing_WHEN_get_identity_THEN_identity_returned(self):
        identity_string = "TEKTRONIX,AFG3021,C100101,SCPI:99.0 FV:1.0"

        self.ca.assert_that_pv_is("IDN", identity_string[:39])  # limited string size

    def test_GIVEN_nothing_WHEN_triggering_device_THEN_device_is_triggered(self):
        self._lewis.backdoor_set_and_assert_set("triggered", "False")
        self.ca.set_pv_value("TRIGGER", True)
        self._lewis.assert_that_emulator_value_is("triggered", "True")

    def _assert_rbv_set(self, pv_name, expected_value):
        self.ca.set_pv_value(f"OUTPUT1:{pv_name}:SP", str(expected_value))
        self.ca.assert_that_pv_is(f"OUTPUT1:{pv_name}", expected_value)
        self.ca.assert_that_pv_is(f"OUTPUT1:{pv_name}:SP:RBV", expected_value)

    def test_GIVEN_scan_macro_set_passive_WHEN_sp_changed_THEN_sp_rbv_changed(self):
        self._assert_rbv_set("FUNC", "RAMP")
        self._assert_rbv_set("IMPEDANCE", 4.0)
        self._assert_rbv_set("POLARITY", "INV")
        self._assert_rbv_set("VOLT", 10.0)
        self._assert_rbv_set("VOLT:UNITS", "VRMS")
        self._assert_rbv_set("VOLT:LOWLIMIT", 1.0)
        self._assert_rbv_set("VOLT:HIGHLIMIT", 3.0)
        self._assert_rbv_set("VOLT:LOW", 2.0)
        self._assert_rbv_set("VOLT:HIGH", 1.5)
        self._assert_rbv_set("VOLT:OFFSET", 10)
        self._assert_rbv_set("FREQ", 5.0)
        self._assert_rbv_set("PHASE", 4)
        self._assert_rbv_set("BURST_STATUS", "OFF")
        self._assert_rbv_set("BURST_MODE", "GAT")
        self._assert_rbv_set("BURST_NCYCLES", 40)
        self._assert_rbv_set("BURST_TDELAY", 9)
        self._assert_rbv_set("FREQ_MODE", "SWE")
        self._assert_rbv_set("SWEEP_SPAN", 30)
        self._assert_rbv_set("SWEEP_START", 20)
        self._assert_rbv_set("SWEEP_STOP", 40)
        self._assert_rbv_set("SWEEP_HTIME", 1)
        self._assert_rbv_set("SWEEP_MODE", "AUTO")
        self._assert_rbv_set("RAMP:SYMMETRY", 42.0)

    def test_GIVEN_arbitrary_command_WHEN_sent_THEN_output_received(self):
        expected_value = 15.0
        self.ca.set_pv_value("WRITE:SP", f"SOUR1:VOLT {expected_value}", wait=True)
        self.ca.set_pv_value("OUTPUT1:VOLT.PROC", 1) # needed as SCAN macro for tests is "Passive"
        self.ca.assert_that_pv_is("OUTPUT1:VOLT", expected_value)
        self.ca.set_pv_value("READ:SP", "SOUR1:VOLT?")
        self.ca.assert_that_pv_is("READ", str(expected_value))
