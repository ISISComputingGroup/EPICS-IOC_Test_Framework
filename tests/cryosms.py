import unittest

from parameterized import parameterized
from utils.test_modes import TestModes
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, IOCRegister
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, parameterized_list

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
            "WRITE_UNIT": "AMPS",
            "DISPLAY_UNIT": "GAUSS",
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


TEST_MODES = [TestModes.DEVSIM]#, TestModes.RECSIM]
TEST_RAMPS = [[(0.0, 10000.0), [1.12]],
              [(5000.0, 25000.0), [1.12, 0.547, 0.038]],
              [(-5000.0, -25000.0), [1.12, 0.547, 0.038]],
              [(25000.0, 5000.0), [0.038, 0.547, 1.12]],
              [(25000.0, -25000.0), [0.038, 0.547, 1.12, 0.547, 0.038]],
              [(-25000.0, 25000.0), [0.038, 0.547, 1.12, 0.547, 0.038]],
              [(-25000.0, 0), [0.038, 0.547, 1.12]],
              [(25000.0, 0), [0.038, 0.547, 1.12]],
              ]


class CryoSMSTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc(EMULATOR_NAME, DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX, default_timeout=10)

        if IOCRegister.uses_rec_sim:
            self.ca.assert_that_pv_exists("DISABLE", timeout=30)
        else:
            self.ca.assert_that_pv_is("INIT", "Startup complete",  timeout=30)
            self.ca.set_pv_value("ABORT:SP", 1)
            self.ca.set_pv_value("MID:SP", 0)
            self._lewis.backdoor_set_on_device("output", 0)
            self.ca.set_pv_value("ABORT:SP", 0)
            self.ca.set_pv_value("START:SP", 1)
            self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON TARGET")
            self.ca.assert_that_pv_is("OUTPUT:RAW", 0)

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

    def test_GIVEN_outputmode_sp_correct_WHEN_outputmode_sp_written_to_THEN_outputmode_changes(self):
        # For all other tests, alongside normal operation, communication should be in amps
        self.ca.assert_setting_setpoint_sets_readback("TESLA", "OUTPUTMODE", "OUTPUTMODE:SP", timeout=10)
        self.ca.assert_setting_setpoint_sets_readback("AMPS", "OUTPUTMODE", "OUTPUTMODE:SP", timeout=10)

    @parameterized.expand(parameterized_list(TEST_RAMPS))
    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_psu_at_field_strength_A_WHEN_told_to_ramp_to_B_THEN_correct_rates_used(self, _, ramp_data):
        startPoint, endPoint = ramp_data[0]
        ramp_rates = ramp_data[1]
        # When setting output, convert from Gauss to Amps by dividing by 10000 and T_TO_A
        self._lewis.backdoor_set_on_device("output", startPoint/(0.037 * 10000))
        self.ca.set_pv_value("MID:SP", endPoint)
        self.ca.set_pv_value("START:SP", 1)
        for rate in ramp_rates:
            self.ca.assert_that_pv_is("RAMP:RATE", rate, timeout=20)
        self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON TARGET", timeout=25)
        self.ca.assert_that_pv_is_within_range("OUTPUT", endPoint - 0.01, endPoint + 0.01)

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_not_ramping_WHEN_ramp_started_THEN_simulated_ramp_performed(self):
        self.ca.set_pv_value("MID:SP", 10000)
        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("RAMP:STAT", "RAMPING", msg="Ramping failed to start")
        self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON TARGET", timeout=10)

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_ramping_WHEN_paused_and_unpaused_THEN_ramp_is_paused_resumed_and_completes(self):
        # GIVEN ramping
        self.ca.set_pv_value("MID:SP", 10000)
        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("RAMP:STAT", "RAMPING")
        # Pauses when pause set to true
        self.ca.set_pv_value("PAUSE:SP", 1)
        self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON PAUSE", msg="Ramping failed to pause")
        self.ca.assert_that_pv_is_not("RAMP:STAT", "HOLDING ON TARGET", timeout=5,
                                      msg="Ramp completed even though it should have paused")
        # Resumes when pause set to false, completes ramp
        self.ca.set_pv_value("PAUSE:SP", 0)
        self.ca.assert_that_pv_is("RAMP:STAT", "RAMPING", msg="Ramping failed to resume")
        self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON TARGET", timeout=10, msg="Ramping failed to complete")

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_ramping_WHEN_aborted_THEN_ramp_aborted(self):
        # Given Ramping
        self.ca.set_pv_value("MID:SP", 10000)
        self.ca.set_pv_value("START:SP", 1)
        self.ca.assert_that_pv_is("RAMP:STAT", "RAMPING")
        # Aborts when abort set to true, then hits ready again
        self.ca.set_pv_value("ABORT:SP", 1)
        self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON TARGET", timeout=10)

    @skip_if_recsim("C++ driver can not correctly initialise in recsim")
    def test_GIVEN_IOC_paused_WHEN_aborted_THEN_ramp_aborted(self):
        # GIVEN paused
        self.ca.set_pv_value("MID:SP", 10000)
        self.ca.set_pv_value("START:SP", 1)
        self.ca.set_pv_value("PAUSE:SP", 1)
        rampTarget = self.ca.get_pv_value("MID")
        self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON PAUSE", msg="Ramping failed to pause")
        # Aborts when abort set to true, then hits ready again
        self.ca.set_pv_value("ABORT:SP", 1)
        self.ca.assert_that_pv_is("RAMP:STAT", "HOLDING ON TARGET", timeout=10)
        self.ca.assert_that_pv_is_not("MID", rampTarget)

    @skip_if_recsim("Test is to tell whether data from emulator is correctly received")
    def test_GIVEN_output_nonzero_WHEN_units_changed_THEN_output_raw_adjusts(self):
        # Check that it is currently working correctly in Amps
        self._lewis.backdoor_set_on_device("is_paused", True)
        self._lewis.backdoor_set_on_device("output", 1/0.037)  # 1T (0.037 = T_TO_A)
        self.ca.assert_that_pv_is_number("OUTPUT:RAW", 1/0.037, 0.001)
        self.ca.assert_that_pv_is_number("OUTPUT", 10000, 1)  # OUTPUT should remain in Gauss
        # Set outputmode to tesla
        self.ca.set_pv_value("OUTPUTMODE:SP", "TESLA")
        self.ca.assert_that_pv_is_number("OUTPUT:RAW", 1, 0.001)
        self.ca.assert_that_pv_is_number("OUTPUT", 10000, 1)
        # Confirm functionality returns to normal when going back to Amps
        self.ca.set_pv_value("OUTPUTMODE:SP", "AMPS")
        self.ca.assert_that_pv_is_number("OUTPUT:RAW", 1/0.037, 0.001)
        self.ca.assert_that_pv_is_number("OUTPUT", 10000, 1)
