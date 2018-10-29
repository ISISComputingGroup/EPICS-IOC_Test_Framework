from __future__ import division
from parameterized import parameterized
import unittest
from time import clock, sleep
import threading

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import parameterized_list

DEVICE_PREFIX = "SEPRTR_01"

MAX_DAQ_VOLT = 10
MAX_SEPARATOR_VOLT = 200
MIN_SEPARATOR_VOLT = 0
DAQ_VOLT_WRITE_SCALE_FACTOR = MAX_DAQ_VOLT / MAX_SEPARATOR_VOLT

MAX_SEPARATOR_CURR = 2.5
DAQ_CURR_READ_SCALE_FACTOR = MAX_SEPARATOR_CURR / MAX_DAQ_VOLT

MARGIN_OF_ERROR = 1e-5

# Voltage and current stability limits
VOLT_LOWERLIM = 0.1
VOLT_UPPERLIM = MAX_SEPARATOR_VOLT

VOLT_STEADY = 0.5*MAX_SEPARATOR_VOLT

CURR_STEADY = 0.5*MAX_SEPARATOR_CURR
CURR_LIMIT = MAX_SEPARATOR_CURR

SAMPLE_LEN = 100
SAMPLETIME = 1.0/float(SAMPLE_LEN)

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("SEPRTR"),
        "macros": {"VUPPERLIM": VOLT_UPPERLIM,
                   "VLOWERLIM": VOLT_LOWERLIM,
                   "ISTEADY": CURR_STEADY,
                   "ILIMIT": CURR_LIMIT
                   },
    },
]

TEST_MODES = [TestModes.RECSIM]


def power_status_set_up(ca):
    """ Sets up the PVs for the power status tests """
    ca.set_pv_value("VOLT:SP", 0.0)
    ca.assert_that_pv_is_number("VOLT:SP", 0.0, tolerance=1e-3)
    ca.assert_that_pv_is("POWER:STAT", "OFF")


def voltage_set_up(ca):
    """ Sets up the PVs for the voltage tests """
    ca.set_pv_value("VOLT:SP", 0.0)
    ca.assert_that_pv_is_number("VOLT:SP", 0.0, tolerance=1e-3)
    ca.set_pv_value("DAQ:VOLT:SIM", 0.0)
    ca.assert_that_pv_is_number("DAQ:VOLT:SIM", 0.0, tolerance=1e-3)
    ca.set_pv_value("DAQ:VOLT:SP", 0.0)
    ca.assert_that_pv_is_number("DAQ:VOLT:SP", 0.0, tolerance=1e-3)
    ca.set_pv_value("DAQ:VOLT:WV:SIM", 0.0)
    ca.assert_that_pv_is_number("VOLT", 0.0, tolerance=1e-3)


def current_set_up(ca):
    """ Sets up the PVs for the current tests """
    ca.set_pv_value("DAQ:CURR:WV:SIM", 0.0)
    ca.assert_that_pv_is_number("CURR", 0.0, tolerance=1e-3)


def stability_set_up(ca):
    """ Sets up the PVs for the separator stability tests """
    ca.set_pv_value("STABILITY", 0.0)
    ca.assert_that_pv_is_number("STABILITY", 0.0, tolerance=1e-3)

    ca.set_pv_value("WINDOWSIZE", 600)
    ca.assert_that_pv_is_number("WINDOWSIZE", 600, tolerance=1e-3)

    ca.set_pv_value("_ADDCOUNTS", 0.0)
    ca.assert_that_pv_is_number("_ADDCOUNTS", 0.0, tolerance=1e-3)

    ca.set_pv_value("RESETWINDOW", 1)

    ca.assert_that_pv_is_number("UNSTABLETIME", 0.0)

    ca.set_pv_value("SAMPLETIME", SAMPLETIME)
    ca.assert_that_pv_is_number("SAMPLETIME", SAMPLETIME)

    ca.set_pv_value("_COUNTERTIMING.SCAN", "1 second")
    ca.assert_that_pv_is("_COUNTERTIMING.SCAN", "1 second")

    ca.set_pv_value("_VOLTCALIBCONST", 1.0/DAQ_VOLT_WRITE_SCALE_FACTOR)
    ca.assert_that_pv_is_number("_VOLTCALIBCONST", 1.0/DAQ_VOLT_WRITE_SCALE_FACTOR, tolerance=1e-3)

    ca.set_pv_value("_CURRCALIBCONST", DAQ_CURR_READ_SCALE_FACTOR)
    ca.assert_that_pv_is_number("_CURRCALIBCONST", DAQ_CURR_READ_SCALE_FACTOR, tolerance=1e-3)

    ca.set_pv_value("THRESHOLD", 0.5)
    ca.assert_that_pv_is_number("THRESHOLD", 0.5, tolerance=1e-3)


def shared_setup(ca):
    """
    Performs initialisation before each test to ensure test independence.

    Returns:
    None
    """

    voltage_set_up(ca)
    power_status_set_up(ca)
    current_set_up(ca)
    stability_set_up(ca)

    return None


def stream_data(ca, n_repeat, curr, volt, stop_event):
    """
    Sends a stream of data over the channel access link. This will attempt n_repeat writes per second.
    Args:
        ca: Object, The channel access link
        n_repeat: integer, The maximum number of writes which will be performed per second
        curr: List of float, The current data to be written over CA
        volt: List of float, The voltage data to be written over CA
        stop_event: threading.Event() object which tells the process to exit

    Returns:

    """
    while not stop_event.is_set():

        for i in range(n_repeat):
            ca.set_pv_value("DAQ:CURR:WV:SIM", curr, wait=True, sleep_after_set=0.0)
            ca.set_pv_value("DAQ:VOLT:WV:SIM", volt, wait=True, sleep_after_set=0.0)

        # This sleep allows the PV to be read with updated value. PV clears once a second.
        sleep(1.1)


def simulate_current_data():
    """
    Generates a set of data around the current stability limit

    Returns:
        current_data: Array of floats

    """

    current_data = [CURR_STEADY]*int(0.75*SAMPLE_LEN)

    current_data.extend([CURR_STEADY+2.0*CURR_LIMIT] * int(0.25*SAMPLE_LEN))

    return current_data


def simulate_voltage_data():
    """
    Generates a set of data around the voltage stability limit

    Returns:
        voltage_data: Array of floats

    """

    voltage_data = [2.0*VOLT_UPPERLIM] * int(0.25*SAMPLE_LEN)

    voltage_data.extend([VOLT_STEADY]*int(0.75*SAMPLE_LEN))

    return voltage_data


CURRENT_DATA = simulate_current_data()
VOLTAGE_DATA = simulate_voltage_data()


# Note that it is difficult to test the Current readback in Recsim because it is only a readback value, and relates
# closely to the voltage.

class PowerStatusTests(unittest.TestCase):
    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        shared_setup(self.ca)

    def test_that_GIVEN_psu_off_WHEN_voltage_setpoint_changed_higher_than_threshold_THEN_psu_status_changes_on(self):
        # GIVEN
        # asserted in setUp
        # WHEN
        self.ca.set_pv_value("VOLT:SP", 100)

        # THEN
        self.ca.assert_that_pv_is("POWER:STAT", "ON")

    def test_that_GIVEN_psu_on_WHEN_voltage_setpoint_changed_lower_than_threshold_THEN_psu_status_changes_off(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 10)
        self.ca.assert_that_pv_is("VOLT", 10)
        self.ca.assert_that_pv_is("POWER:STAT", "ON")

        # WHEN
        self.ca.set_pv_value("VOLT:SP", 0)

        # THEN
        self.ca.assert_that_pv_is("POWER:STAT", "OFF")


class VoltageTests(unittest.TestCase):
    voltage_values = [0, 10.1111111, 10e1, 20e-2, 200]
    voltage_values_which_give_alarms = [-50, MIN_SEPARATOR_VOLT, MAX_SEPARATOR_VOLT, 250]

    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        shared_setup(self.ca)

    def test_that_GIVEN_sim_val_0_and_data_0_WHEN_voltage_set_point_changed_THEN_data_changed(self):
        # GIVEN
        self.ca.set_pv_value("DAQ:VOLT:SIM", 0)
        self.ca.assert_that_pv_is("DAQ:VOLT:SP", 0)

        # WHEN
        self.ca.set_pv_value("VOLT:SP", 20.)

        # THEN
        self.ca.assert_that_pv_is("DAQ:VOLT:SP", 20. * DAQ_VOLT_WRITE_SCALE_FACTOR)

    @parameterized.expand(parameterized_list(voltage_values))
    def test_that_WHEN_set_THEN_the_voltage_changes(self, _, value):
        # WHEN
        self.ca.set_pv_value("VOLT:SP", value)

        # THEN
        self.ca.assert_that_pv_is_number("VOLT", value, MARGIN_OF_ERROR)

    @parameterized.expand(parameterized_list(voltage_values_which_give_alarms))
    def test_that_WHEN_voltage_out_of_range_THEN_alarm_raised(self, _, value):
        # WHEN

        self.ca.set_pv_value("VOLT:SP", value)

        # THEN
        self.ca.assert_that_pv_alarm_is("VOLT", ChannelAccess.Alarms.MAJOR)

    def test_that_GIVEN_voltage_in_range_WHEN_setpoint_is_above_range_THEN_setpoint_is_set_to_max_value(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 30)
        self.ca.assert_that_pv_is("VOLT", 30)

        # WHEN
        self.ca.set_pv_value("VOLT:SP", 215.)

        # THEN
        self.ca.assert_that_pv_is("VOLT:SP", MAX_SEPARATOR_VOLT)
        self.ca.assert_that_pv_is("VOLT", MAX_SEPARATOR_VOLT)

    def test_that_GIVEN_voltage_in_range_WHEN_setpoint_is_below_range_THEN_setpoint_is_set_to_min_value(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 30)
        self.ca.assert_that_pv_is("VOLT", 30)

        # WHEN
        self.ca.set_pv_value("VOLT:SP", -50)

        # THEN
        self.ca.assert_that_pv_is("VOLT", MIN_SEPARATOR_VOLT)
        self.ca.assert_that_pv_is("VOLT:SP", MIN_SEPARATOR_VOLT)


class CurrentTests(unittest.TestCase):
    # These current testing values are uncalibrated values from the DAQ lying between 0 and 10.
    current_values = [0, 1.33333, 5e1, 10e-3, 10]
    current_values_which_give_alarms = [-2, 0, 10, 11]

    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        shared_setup(self.ca)
        self._simulate_current(0)

    def _simulate_current(self, current):
        curr_array = [current] * 1000
        self.ca.set_pv_value("DAQ:CURR:WV:SIM", curr_array)

    @parameterized.expand(parameterized_list(current_values))
    def test_that_GIVEN_current_value_THEN_calibrated_current_readback_changes(self, _, value):
        # GIVEN
        self._simulate_current(value)

        self.ca.assert_that_pv_is_number("CURR", value * DAQ_CURR_READ_SCALE_FACTOR, MARGIN_OF_ERROR)

    @parameterized.expand(parameterized_list(current_values_which_give_alarms))
    def test_that_WHEN_current_is_out_of_range_THEN_alarm_raised(self, _, value):
        # WHEN
        self._simulate_current(value)

        # THEN
        self.ca.assert_that_pv_alarm_is("CURR", ChannelAccess.Alarms.MAJOR)


class StabilityTests(unittest.TestCase):
    STOP_DATA_THREAD = threading.Event()

    def setUp(self):
        self.ca = ChannelAccess(20, device_prefix=DEVICE_PREFIX)
        shared_setup(self.ca)

        self.STOP_DATA_THREAD.set()

    @staticmethod
    def evaluate_current_instability(current_values):
        """
        Evaluates the input current values against the stability criterion.

        Args:
            current_values: Array of input currents

        Returns:
            current_instability: Boolean array of len(current_values). True where element is unstable, else False

        """

        current_instability = [curr_measured >= (CURR_STEADY + CURR_LIMIT) for curr_measured in current_values]

        return current_instability

    @staticmethod
    def evaluate_voltage_instability(voltage_values):
        """
        Evaluates the input voltages against the stability criterion.

        Args:
            voltage_values: Array of input voltages

        Returns:
            voltage_instability: Boolean array of len(voltage_values). True where element is unstable, else False

        """

        voltage_instability = [(VOLT_LOWERLIM >= volt_measured) or (volt_measured >= VOLT_UPPERLIM) for volt_measured in voltage_values]

        return voltage_instability

    def get_out_of_range_samples(self, current_values, voltage_values):
        """
        Calculates the number of points which lie out of stability limits for a current and voltage dataset.
        Args:
            current_values: Array of input current values
            voltage_values: Array of input voltage values

        Returns:
            out_of_range_count: Integer, the number of samples in the dataset which are out of range

        """

        current_instability = self.evaluate_current_instability(current_values)
        voltage_instability = self.evaluate_voltage_instability(voltage_values)

        overall_instability = [curr or volt for curr, volt in zip(current_instability, voltage_instability)]

        out_of_range_count = sum(overall_instability)

        return out_of_range_count

    def write_simulated_current(self, curr_data):
        """ Scales a current waveform to the DAQ voltage range and writes to current simulation PV

        Inputs:
            curr_data: list of floats containing the current data in engineering units
        """
        scaled_data = [x / DAQ_CURR_READ_SCALE_FACTOR for x in curr_data]
        self.ca.set_pv_value("DAQ:CURR:WV:SIM", scaled_data, wait=True, sleep_after_set=0.0)

    def write_simulated_voltage(self, volt_data):
        """ Scales a voltage waveform to the DAQ voltage range and writes to voltage simulation PV

        Inputs:
            volt_data: list of floats containing the voltage data in engineering units
        """
        scaled_data = [x * DAQ_VOLT_WRITE_SCALE_FACTOR for x in volt_data]

        self.ca.set_pv_value("DAQ:VOLT:WV:SIM", scaled_data, wait=True, sleep_after_set=0.0)

    @parameterized.expand([
        ("steady_current_steady_voltage", [CURR_STEADY]*SAMPLE_LEN, [VOLT_STEADY]*SAMPLE_LEN),

        ("steady_current_unsteady_voltage", [CURR_STEADY] * SAMPLE_LEN, VOLTAGE_DATA),

        ("unsteady_current_steady_voltage", CURRENT_DATA, [VOLT_STEADY] * SAMPLE_LEN),

        ("unsteady_current_and_voltage", simulate_current_data(), simulate_voltage_data())
    ])
    def test_GIVEN_current_and_voltage_data_WHEN_limits_are_tested_THEN_number_of_samples_out_of_range_returned(self, _, curr_data, volt_data):
        self.write_simulated_current(curr_data)
        self.write_simulated_voltage(volt_data)

        expected_out_of_range_samples = self.get_out_of_range_samples(curr_data, volt_data)

        self.ca.assert_that_pv_is_number("_STABILITYCHECK", expected_out_of_range_samples, tolerance=0.05*expected_out_of_range_samples)

    @parameterized.expand([
        ("unsteady_current", simulate_current_data(), [VOLT_STEADY] * SAMPLE_LEN),
        ("unsteady_voltage", [CURR_STEADY] * SAMPLE_LEN, simulate_voltage_data())

    ])
    def test_GIVEN_multiple_samples_in_one_second_WHEN_buffer_read_THEN_buffer_reads_all_out_of_range_samples(self, _, curr_data, volt_data):

        # Setting this to 3 as channel access takes ~0.25s. May need lowering for slow machines.
        writes_per_second = 3

        expected_out_of_range_samples = self.get_out_of_range_samples(curr_data, volt_data) * writes_per_second

        self.STOP_DATA_THREAD.clear()

        scaled_curr_data = [x / DAQ_CURR_READ_SCALE_FACTOR for x in curr_data]
        scaled_volt_data = [x * DAQ_VOLT_WRITE_SCALE_FACTOR for x in volt_data]

        data_supply_thread = threading.Thread(target=stream_data,
                                              args=(self.ca, writes_per_second, scaled_curr_data, scaled_volt_data, self.STOP_DATA_THREAD))

        # GIVEN
        data_supply_thread.start()

        self.assertGreater(writes_per_second, 1)

        # THEN
        self.ca.assert_that_pv_is_number("_ADDCOUNTS", expected_out_of_range_samples, timeout=60.0)

        self.STOP_DATA_THREAD.set()

    def test_GIVEN_buffer_with_data_WHEN_resetwindow_PV_processed_THEN_buffer_is_cleared(self):
        number_of_writes = 50

        expected_out_of_range_samples = self.get_out_of_range_samples(CURRENT_DATA,
                                                                      VOLTAGE_DATA) * number_of_writes * SAMPLETIME

        # GIVEN
        for i in range(number_of_writes):
            self.write_simulated_current(CURRENT_DATA)
            self.write_simulated_voltage(VOLTAGE_DATA)

        self.ca.assert_that_pv_is_number("UNSTABLETIME", expected_out_of_range_samples)

        # WHEN
        self.ca.set_pv_value("RESETWINDOW", 1)

        # THEN
        self.ca.assert_that_pv_is_number("UNSTABLETIME", 0)

    def test_GIVEN_full_buffer_WHEN_more_data_added_to_buffer_THEN_oldest_values_overwritten(self):
        length_of_buffer = 10
        testvalue = 50.0

        self.assertNotEqual(testvalue, 1.0)

        self.ca.set_pv_value("WINDOWSIZE", length_of_buffer)
        self.ca.set_pv_value("RESETWINDOW", 1)

        self.ca.set_pv_value("_COUNTERTIMING.SCAN", "Passive")

        # GIVEN

        for i in range(length_of_buffer):
            self.ca.set_pv_value("_ADDCOUNTS", 1.0/SAMPLETIME, wait=True, sleep_after_set=0.0)

            self.ca.set_pv_value("_COUNTERTIMING.PROC", 1, wait=True, sleep_after_set=0.0)

        self.ca.assert_that_pv_is_number("UNSTABLETIME", length_of_buffer)

        # WHEN
        self.ca.set_pv_value("_ADDCOUNTS", testvalue / SAMPLETIME, wait=True, sleep_after_set=0.0)
        self.ca.set_pv_value("_COUNTERTIMING.PROC", 1, wait=True, sleep_after_set=0.0)

        # THEN
        self.ca.assert_that_pv_is_number("UNSTABLETIME", (length_of_buffer-1.)+testvalue)

    def test_GIVEN_input_data_over_several_seconds_WHEN_stability_PV_read_THEN_all_unstable_time_counted(self):
        # This number needs to be large enough to write over several seconds. Writing over multiple seconds is asserted.
        number_of_writes = 50

        time1 = clock()

        expected_out_of_range_samples = self.get_out_of_range_samples(CURRENT_DATA,
                                                                      VOLTAGE_DATA) * number_of_writes * SAMPLETIME

        # GIVEN
        for i in range(number_of_writes):
            self.write_simulated_current(CURRENT_DATA)
            self.write_simulated_voltage(VOLTAGE_DATA)

        processtime = clock() - time1
        self.assertGreater(processtime, 1.)

        # THEN
        self.ca.assert_that_pv_is_number("UNSTABLETIME", expected_out_of_range_samples,
                                         tolerance=0.05*expected_out_of_range_samples)

    def test_GIVEN_power_supply_switched_on_WHEN_power_supply_out_of_stability_threshold_THEN_stability_PV_equals_zero_and_goes_into_alarm(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 10)
        self.ca.assert_that_pv_is("POWER:STAT", "ON")

        # WHEN
        stability_threshold = self.ca.get_pv_value("THRESHOLD")

        testvalue = stability_threshold * 100

        self.ca.set_pv_value("_ADDCOUNTS", testvalue / SAMPLETIME, wait=True, sleep_after_set=0.0)

        self.ca.assert_that_pv_is_number("STABILITY", 0, tolerance=0.1)

        # THEN
        self.ca.assert_that_pv_alarm_is("STABILITY", ChannelAccess.Alarms.MAJOR)

    def test_GIVEN_power_supply_switched_off_WHEN_power_supply_out_of_stability_threshold_THEN_no_alarms_raised(self):
        # GIVEN
        self.ca.set_pv_value("VOLT:SP", 0)
        self.ca.assert_that_pv_is("POWER:STAT", "OFF")

        # WHEN
        stability_threshold = self.ca.get_pv_value("THRESHOLD")

        testvalue = stability_threshold * 100

        self.ca.set_pv_value("_ADDCOUNTS", testvalue / SAMPLETIME, wait=True, sleep_after_set=0.0)

        self.ca.assert_that_pv_is_number("STABILITY", 0, tolerance=0.1)

        # THEN
        self.ca.assert_that_pv_alarm_is("STABILITY", ChannelAccess.Alarms.NONE)
