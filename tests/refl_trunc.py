import os
from time import sleep
import unittest

from parameterized import parameterized
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister, get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import assert_log_messages, parameterized_list


GALIL_ADDR1 = "127.0.0.11"
GALIL_ADDR2 = "127.0.0.12"
GALIL_PREFIX = "GALIL_01"
GALIL_PREFIX_JAWS = "GALIL_02"


ioc_number = 1
DEVICE_PREFIX = "REFL_{:02d}".format(ioc_number)
test_config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_config", "good_for_refl"))


IOCS = [
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": GALIL_PREFIX,
        "custom_prefix": "MOT",
        "directory": get_default_ioc_dir("GALIL"),
        "pv_for_existence": "MTR0101",
        "macros": {
            "GALILADDR": GALIL_ADDR1,
            "MTRCTRL": "1",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
        "delay_after_startup": 5
    },
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": GALIL_PREFIX_JAWS,
        "custom_prefix": "MOT",
        "directory": get_default_ioc_dir("GALIL", iocnum=2),
        "pv_for_existence": "MTR0201",
        "macros": {
            "GALILADDR": GALIL_ADDR2,
            "MTRCTRL": "2",
            "GALILCONFIGDIR": test_config_path.replace("\\", "/"),
        },
        "delay_after_startup": 5
    },
    {
        "ioc_launcher_class": ProcServLauncher,
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("REFL", iocnum=ioc_number),
        "started_text": "Reflectometry IOC started",
        "pv_for_existence": "STAT",
        "macros": {
            "CONFIG_FILE": "config_trunc.py"
        },
        "environment_vars": {
            "IOC_TEST": "1",
            "ICPCONFIGROOT": test_config_path
        }
    }
]


TEST_MODES = [TestModes.DEVSIM]


WAVEFORM_PVS = [
    ("PARAM_INFO",     2048),
    ("COLLIM_INFO",    2048),
    ("TOGGLE_INFO",    2048),
    ("SLIT_INFO",      2048),
    ("MISC_INFO",      2048),
    ("FOOTPRINT_INFO", 2048),
    ("CONST_INFO",     2048),
    ("ALIGN_INFO",     2048)
]


class ReflTests(unittest.TestCase):
    """
    Tests for reflectometry server
    """
    
    def setUp(self):
        self._ioc = IOCRegister.get_running(DEVICE_PREFIX)
        self.ca = ChannelAccess(default_timeout=30, device_prefix=DEVICE_PREFIX)

    @parameterized.expand(parameterized_list(WAVEFORM_PVS))
    def test_GIVEN_saturated_configuration_WHEN_waveform_pv_read_THEN_value_truncated(self, _, pv, max_size):
        size = len(self.ca.get_pv_value(pv))
        self.assertEqual(size, max_size, f"PARAM_INFO size {size} should be {max_size}.")

    def test_WHEN_server_message_exceeds_character_limit_THEN_message_truncated_correctly(self):
        SERVER_MESSAGE_MAX_SIZE = 400

        self.ca.set_pv_value("PARAM:INBEAM:SP", 0, wait=True)
        sleep(2)

        message : str = self.ca.get_pv_value("MSG")
        self.assertTrue(message.endswith("<truncated>"), f"Server message has to end with '<truncated>'.\nMESSAGE:\n{message}")
        self.assertEqual(len(message), SERVER_MESSAGE_MAX_SIZE, f"Server Message size {len(message)} should be {SERVER_MESSAGE_MAX_SIZE}.\nMESSAGE:\n{message}")

    def test_WHEN_log_error_messages_exceed_character_limit_THEN_log_truncated_correctly(self):
        ERROR_LOG_MAX_SIZE = 10_000
        ERROR_MESSAGE = "Error: PV FOOTPRINT_INFO is read only"
        NUM_ERROR_MESSAGES = int((ERROR_LOG_MAX_SIZE / len(ERROR_MESSAGE)) * 1.2)
        
        with assert_log_messages(self._ioc, in_time=20) as cm:
            for _ in range(NUM_ERROR_MESSAGES):
                self.ca.set_pv_value("FOOTPRINT_INFO", "")

        count = 0
        for message in cm.messages:
            if ERROR_MESSAGE in message:
                count +=1
        self.assertEqual(count, NUM_ERROR_MESSAGES, f"Expected {NUM_ERROR_MESSAGES} got {count} number of error messages.")

        size = len(self.ca.get_pv_value("LOG"))
        self.assertEqual(size, ERROR_LOG_MAX_SIZE, f"Error log with size {size} should be {ERROR_LOG_MAX_SIZE}.")
