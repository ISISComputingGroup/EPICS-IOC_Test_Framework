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

# IOC has no SIM records
TEST_MODES = [TestModes.DEVSIM]


class ChtobisrTests(unittest.TestCase):
    """
        Tests for the Coherent OBIS Laser Remote IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=30)
        self._lewis.backdoor_set_on_device("connected", True)
        self._lewis.backdoor_run_function_on_device("reset")

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
        self.ca.assert_that_pv_is("INTERLOCK", "CLOSED")
        self._lewis.backdoor_run_function_on_device("reset")
        self.ca.assert_that_pv_is("INTERLOCK", "OPEN")

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_reset_requested_WHEN_device_connected_THEN_device_is_reset(self):
        self._lewis.backdoor_set_on_device("interlock", "ON")
        self.ca.assert_that_pv_is("INTERLOCK", "CLOSED")
        self.ca.set_pv_value("RESET:SP", "TRUE")
        self.ca.assert_that_pv_is("INTERLOCK", "OPEN")

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_interlock_status_requested_WHEN_device_connected_THEN_interlock_status_is_returned(self):
        self._lewis.backdoor_set_on_device("interlock", "OFF")
        self.ca.assert_that_pv_is("INTERLOCK", "OPEN")

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_status_requested_WHEN_lowest_status_bit_set_THEN_correct_status_code_is_returned(self):
        expected_value = 0x0001
        self._lewis.backdoor_run_function_on_device("backdoor_set_status", ["laser_fault", True])
        self.ca.assert_that_pv_is("STAT:LOW.VAL", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_status_requested_WHEN_highest_status_bit_set_THEN_correct_status_code_is_returned(self):
        expected_value = 0x8000
        self._lewis.backdoor_run_function_on_device("backdoor_set_status", ["controller_indicator", True])
        self.ca.assert_that_pv_is("STAT:HIGH.VAL", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_faults_requested_WHEN_lowest_fault_bit_set_THEN_correct_fault_code_is_returned(self):
        expected_value = 0x0001
        self._lewis.backdoor_run_function_on_device("backdoor_set_fault", ["base_plate_temp_fault", True])
        self.ca.assert_that_pv_is("FAULT:LOW.VAL", expected_value)

    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_faults_requested_WHEN_highest_fault_bit_set_THEN_correct_fault_code_is_returned(self):
        expected_value = 0x8000
        self._lewis.backdoor_run_function_on_device("backdoor_set_fault", ["controller_status", True])
        self.ca.assert_that_pv_is("FAULT:HIGH.VAL", expected_value)

    @parameterized.expand(parameterized_list([
        ("laser_fault",             "STAT:LASER:FAULT"),            
        ("laser_emission",          "STAT:LASER:EMISSION"),         
        ("laser_ready",             "STAT:LASER:READY"),            
        ("laser_standby",           "STAT:LASER:STANDBY"),          
        ("cdrh_delay",              "STAT:LASER:CDRHDELAY"),        
        ("laser_hardware_fault",    "STAT:LASER:HWFAULT"),          
        ("laser_error",             "STAT:LASER:ERROR"),            
        ("laser_power_calibration", "STAT:LASER:POWERCALIB"),       
        ("laser_warm_up",           "STAT:LASER:WARMUP"),           
        ("laser_noise",             "STAT:LASER:NOISE"),            
        ("external_operating_mode", "STAT:LASER:EXTERNALOPERATING"),
        ("field_calibration",       "STAT:LASER:FIELDCALIB"),       
        ("laser_power_voltage",     "STAT:LASER:POWERVOLTAGE"),     
        ("controller_standby",      "STAT:CONTROLLER:STANDBY"),     
        ("controller_interlock",    "STAT:CONTROLLER:INTERLOCK"),   
        ("controller_enumeration",  "STAT:CONTROLLER:ENUMERATION"), 
        ("controller_error",        "STAT:CONTROLLER:ERROR"),       
        ("controller_fault",        "STAT:CONTROLLER:FAULT"),       
        ("remote_active",           "STAT:CONTROLLER:REMOTEACTIVE"),
        ("controller_indicator",    "STAT:CONTROLLER:INDICATOR"),   
    ]))
    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_status_active_WHEN_read_status_THEN_pv_reads_status_state(self, _, backdoor_name, pv_name):
        for state in [False, True]:
            self._lewis.backdoor_run_function_on_device("backdoor_set_status", [backdoor_name, state])
            self.ca.assert_that_pv_is(pv_name, str(state))

    @parameterized.expand(parameterized_list([
        ("base_plate_temp_fault",    "FAULT:LASER:BASEPLATETEMP"),
        ("diode_temp_fault",         "FAULT:LASER:DIODETEMP"),
        ("internal_temp_fault",      "FAULT:LASER:INTERNALTEMP"),
        ("laser_power_supply_fault", "FAULT:LASER:PSU"),
        ("i2c_error",                "FAULT:LASER:I2CBUS"),
        ("over_current",             "FAULT:LASER:OVERCURRENT"),
        ("laser_checksum_error",     "FAULT:LASER:CHECKSUM"),
        ("checksum_recovery",        "FAULT:LASER:CHECKSUMRECOVERY"),
        ("buffer_overflow",          "FAULT:LASER:BUFFEROVERFLOW"),
        ("warm_up_limit_fault",      "FAULT:LASER:WARMUPLIMIT"),
        ("tec_driver_error",         "FAULT:LASER:TECDRIVER"),
        ("ccb_error",                "FAULT:LASER:CCBERROR"),
        ("diode_temp_limit_error",   "FAULT:LASER:DIODETEMPLIMIT"),
        ("laser_ready_fault",        "FAULT:LASER:READY"),
        ("photodiode_fault",         "FAULT:LASER:PHOTODIODE"),
        ("fatal_fault",              "FAULT:LASER:FATAL"),
        ("startup_fault",            "FAULT:LASER:STARTUP"),
        ("watchdog_timer_reset",     "FAULT:LASER:WATCHDOG"),
        ("field_calibration",        "FAULT:LASER:FIELDCALIB"),
        ("over_power",               "FAULT:LASER:OVERPOWER"),
        ("controller_checksum",      "FAULT:CONTROLLER:CHECKSUM"),
        ("controller_status",        "FAULT:CONTROLLER:STATUS"),
    ]))
    @skip_if_recsim("Lewis backdoor not available in RecSim")
    def test_GIVEN_fault_active_WHEN_read_faults_THEN_pv_reads_fault_state(self, _, backdoor_name, pv_name):
        for state in [False, True]:
            self._lewis.backdoor_run_function_on_device("backdoor_set_fault", [backdoor_name, state])
            self.ca.assert_that_pv_is(pv_name, str(state))
