import unittest

from parameterized import parameterized
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

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
            "RAMP_FILE": "C:\\Instrument\\Apps\\EPICS\\support\\cryosms\\master\\ramps\\test.txt",
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


TEST_MODES = [TestModes.DEVSIM, TestModes.RECSIM]


class CryoSMSTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

        if IOCRegister.uses_rec_sim:
            self.ca.assert_that_pv_exists("DISABLE", timeout=30)
        else:
            self.ca.assert_that_pv_is("INIT", "Startup complete",  timeout=30)

    @skip_if_recsim("Cannot properly simulate device startup in recsim")
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
                          "HEATER:STAT": "OFF",
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

    @parameterized.expand(["TESLA", "AMPS"])
    def test_GIVEN_outputmode_sp_correct_WHEN_outputmode_sp_written_to_THEN_outputmode_changes(self, units):
        self.ca.assert_setting_setpoint_sets_readback(units, "OUTPUTMODE", "OUTPUTMODE:SP", timeout=10)

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_not_ramping_WHEN_ramp_started_THEN_simulated_ramp_performed(self):
        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("QSM:STATE", "RAMPING", msg="Ramping failed to start")
        self.ca.assert_that_pv_is("QSM:STATE", "HOLDING ON TARGET", timeout=10)

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_ramping_WHEN_paused_and_unpaused_THEN_ramp_is_paused_resumed_and_completes(self):
        # GIVEN ramping
        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("QSM:STATE", "RAMPING")
        # Pauses when pause set to true
        self.ca.set_pv_value("PAUSE:SP", 1)
        self.ca.assert_that_pv_is("QSM:STATE", "HOLDING ON PAUSE", msg="Ramping failed to pause")
        self.ca.assert_that_pv_is_not("RAMP:STAT", "HOLDING ON TARGET", timeout=10,
                                      msg="Ramp completed even though it should have paused")
        # Resumes when pause set to false, completes ramp
        self.ca.set_pv_value("PAUSE:SP", 0)
        self.ca.assert_that_pv_is("QSM:STATE", "RAMPING", msg="Ramping failed to resume")
        self.ca.assert_that_pv_is("QSM:STATE", "HOLDING ON TARGET", timeout=10, msg="Ramping failed to complete")

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_ramping_WHEN_aborted_THEN_ramp_aborted(self):
        # Given Ramping
        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("QSM:STATE", "RAMPING")
        # Aborts when abort set to true, then hits ready again
        self.ca.set_pv_value("ABORT:SP", 1)
        self.ca.assert_that_pv_is("QSM:STATE", "HOLDING ON TARGET")

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_paused_WHEN_aborted_THEN_ramp_aborted(self):
        # GIVEN paused
        self.ca.set_pv_value("START:SP", 1)
        self.ca.set_pv_value("PAUSE:SP", 1)
        self.ca.assert_that_pv_is("QSM:STATE", "HOLDING ON PAUSE", msg="Ramping failed to pause")
        # Aborts when abort set to true, then hits ready again
        self.ca.set_pv_value("ABORT:SP", 1)
        self.ca.assert_that_pv_is("QSM:STATE", "HOLDING ON TARGET")
