import unittest

from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "CRYOSMS_01"
EMULATOR_NAME = "cryogenic_sms"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("CRYOSMS"),
        "emulator": EMULATOR_NAME,
        "macros": {
            "MAX_CURR": 135,
            "T_TO_A": 0.037,
            "MAX_VOLT": 9.9,
            "WRITE_UNIT": "Amps",
            "DISPLAY_UNIT": "Gauss",
            "RAMP_FILE": "C:\\Instrument\\Apps\\EPICS\\support\\cryosms\\master\\testramp\\test.txt",
            "MID_TOLERANCE": 0.1,
            "TARGET_TOLERANCE": 0.01,
            "ALLOW_PERSIST": "No",
            "USE_SWITCH": "No",
            "USE_MAGNET_TEMP": "No",
            "COMP_OFF_ACT": "No",
            "HOLD_TIME_ZERO": 12,
            "HOLD_TIME": 30,
            "VOLT_STABILITY_DURATION": 300,
            "VOLT_TOLERANCE": 0.2,
            "FAST_RATE": 0.5,
            "RESTORE_WRITE_UNIT_TIMEOUT": 10,
        }
    },
]


TEST_MODES = [TestModes.DEVSIM]


class CryoSMSTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

        self.ca.assert_that_pv_exists("DISABLE", timeout=30)


    def test_GIVEN_outputmode_sp_correct_WHEN_outputmode_sp_written_to_THEN_outputmode_changes(self):
        # GIVEN
        current_outputmode = self.ca.get_pv_value("OUTPUTMODE")
        self.ca.assert_that_pv_is("OUTPUTMODE:SP", current_outputmode, timeout=30)

        # WHEN
        new_outputmode = "AMPS" if current_outputmode == "TESLA" else "TESLA"
        self.ca.set_pv_value("OUTPUTMODE:SP", new_outputmode)

        # THEN
        self.ca.assert_that_pv_is("OUTPUTMODE:SP", new_outputmode, timeout=10)

    def test_GIVEN_certain_macros_WHEN_IOC_loads_THEN_correct_values_initialised(self):
        expectedValues = {"OUTPUT:SP": 0,
                          "OUTPUT": 0,
                          "OUTPUT:COIL": 0,
                          "OUTPUT:PERSIST": 0,
                          "OUTPUT:VOLT": 0,
                          "RAMP:RATE": 1.12,
                          "READY": 1,
                          "RAMP:RAMPING": 0,
                          "TARGET:TIME": 0,
                          "STAT": "",
                          "HEATER:STAT": "Off",
                          "START:SP.DISP": "0",
                          "PAUSE:SP.DISP": "0",
                          "ABORT:SP.DISP": "0",
                          "OUTPUT:SP.DISP": "0",
                          "MAGNET:MODE.DISP": "1",
                          "RAMP:LEADS.DISP": "1",
                          }
        failedPVs = []
        for PV in expectedValues:
            try:
                self.ca.assert_that_pv_is(PV, expectedValues[PV], timeout=5)
            except Exception as e:
                failedPVs.append(e.message)
        if failedPVs:
            self.fail("The following PVs generated errors:\n{}".format("\n".join(failedPVs)))
