import unittest

from parameterized import parameterized

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

DEVICE_PREFIX = "CHTOBISR_01"
EMULATOR = "chtobisr"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CHTOBISR"),
        "emulator": EMULATOR,
    },
]


# TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]
TEST_MODES = [TestModes.DEVSIM]

ON_OFF = {True: "ON", False: "OFF"}


class ChtobisrTests(unittest.TestCase):
    """
    Tests for the Coherent OBIS Laser Remote IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
        self._lewis.backdoor_set_on_device("connected", True)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_ID_requested_WHEN_device_connected_THEN_ID_is_returned(self):
        expected_value = "Coherent OBIS Laser Remote - EMULATOR"
        self._lewis.backdoor_set_on_device("id", expected_value)
        self.ca.assert_that_pv_is("ID", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_ID_requested_WHEN_device_disconnected_THEN_alarm_is_raised(self):
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("ID", self.ca.Alarms.INVALID)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_reset_requested_THEN_emulator_is_reset(self):
        self._lewis.backdoor_set_on_device("interlock", "ON")
        self.ca.assert_that_pv_is("INTERLOCK:STAT", "ON")
        self._lewis.backdoor_run_function_on_device("reset")
        self.ca.assert_that_pv_is("INTERLOCK:STAT", "OFF")

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_reset_requested_WHEN_device_connected_THEN_device_is_reset(self):
        self._lewis.backdoor_set_on_device("interlock", "ON")
        self.ca.assert_that_pv_is("INTERLOCK:STAT", "ON")
        self.ca.set_pv_value("RESET", "1")
        self.ca.assert_that_pv_is("INTERLOCK:STAT", "OFF")

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_interlock_status_requested_WHEN_device_connected_THEN_interlock_status_is_returned(self):
        expected_value = "ON"
        self._lewis.backdoor_set_on_device("interlock", expected_value)
        self.ca.assert_that_pv_is("INTERLOCK:STAT", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_status_requested_WHEN_device_connected__AND_laser_fault_set_THEN_correct_status_code_is_returned(self):
        expected_value = 0x1
        self._lewis.backdoor_run_function_on_device("backdoor_set_status", ["laser_fault", True])
        self.ca.assert_that_pv_is("STAT:LOW.VAL", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_faults_requested_WHEN_device_connected__AND_base_plate_temp_fault_set_THEN_correct_fault_code_is_returned(self):
        expected_value = 0x1
        self._lewis.backdoor_run_function_on_device("backdoor_set_fault", ["base_plate_temp_fault", True])
        self.ca.assert_that_pv_is("FAULT:LOW.VAL", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_base_plate_temperature_fault_state_WHEN_read_faults_THEN_pv_reads_correct_fault_state(self):
        for state in ["False", "True"]:
            self._lewis.backdoor_run_function_on_device("backdoor_set_fault", ["base_plate_temp_fault", state])
            self.ca.assert_that_pv_is("FAULT:BASEPLATETEMP", state)

    # @parameterized.expand(parameterized_list([
    #     ("base_plate_temp_fault", "FAULT:BASEPLATETEMP"),
    #     ("...", "FAULT:..."),
    # ]))
    # @skip_if_recsim("Lewis backdoor not available in RecSim")
    # def test_GIVEN_fault_active_WHEN_read_faults_THEN_pv_reads_fault_active(self, _, backdoor_name, pv_name):
    #     for state in [False, True]:
    #         self._lewis.backdoor_run_function_on_device("backdoor_set_fault", ["backdoor_name", state])
    #         self.ca.assert_that_pv_is(pv_name, state)
