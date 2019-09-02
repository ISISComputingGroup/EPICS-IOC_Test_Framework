import unittest
import six

from abc import ABCMeta, abstractmethod

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc

from parameterized import parameterized

DEVICE_PREFIX = "EDTIC_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("EDTIC"),
        "macros": {
            "USEGAUGE1": "YES",
            "USEGAUGE2": "YES",
            "USEGAUGE3": "YES"
        },
        "emulator": "edwardstic",
    },
]

# No recsim as this device makes heavy use of record redirection
TEST_MODES = [TestModes.DEVSIM, ]


PRI_SEVERITIES = {"OK": ChannelAccess.Alarms.NONE,
                  "Warning": ChannelAccess.Alarms.MINOR,
                  "Alarm": ChannelAccess.Alarms.MAJOR,
                  }


@six.add_metaclass(ABCMeta)
class EdwardsTICBase(object):
    @abstractmethod
    def get_base_PV(self):
        """
        Returns string containing a PV which is read from the device
        """
        pass

    @abstractmethod
    def get_alert_PV(self):
        """
        Returns string containing the alert PV read through record redirection from the base PV
        """
        pass

    @abstractmethod
    def get_priority_PV(self):
        """
        Returns string containing the priority PV read through record redirection from the base PV
        """
        pass

    @abstractmethod
    def get_status_setter(self):
        """
        Returns string containing the name of the setter function for the base PV in the device emulator
        """
        pass

    @abstractmethod
    def get_alert_function(self):
        """
        Returns string containing the name of the setter function for the alert in the device emulator
        """
        pass

    @abstractmethod
    def get_priority_function(self):
        """
        Returns string containing the name of the setter function for the priority in the device emulator
        """
        pass

    @abstractmethod
    def get_status_labels():
        """
        Returns list of tuples containing:
        (
            string of representation of status in device emulator,
            string of representation of status in IOC,
            expected alarm level for this status
        )
        """
        return ()

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("edwardstic", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("is_connected", True)

    @parameterized.expand([
        (0, ChannelAccess.Alarms.NONE),
        (1, ChannelAccess.Alarms.MINOR),
        (-1, ChannelAccess.Alarms.MAJOR),
        (48, ChannelAccess.Alarms.MAJOR)
    ])
    def test_GIVEN_turbo_status_with_alert_WHEN_turbo_status_read_THEN_turbo_status_alert_is_read_back(self, alert_state, expected_alarm):
        # GIVEN
        self._lewis.backdoor_run_function_on_device(self.get_alert_function(), arguments=(alert_state,))

        # THEN
        self.ca.assert_that_pv_is(self.get_alert_PV(), alert_state)
        self.ca.assert_that_pv_alarm_is(self.get_alert_PV(), expected_alarm)

    @parameterized.expand([
        [key, value] for key, value in PRI_SEVERITIES.items()
    ])
    def test_GIVEN_turbo_status_with_priority_WHEN_turbo_status_read_THEN_turbo_status_priority_is_read_back(self, priority_state, expected_alarm):
        # GIVEN
        self._lewis.backdoor_run_function_on_device(self.get_priority_function(), arguments=(priority_state, ))

        # THEN
        self.ca.assert_that_pv_is(self.get_priority_PV(), priority_state)
        self.ca.assert_that_pv_alarm_is(self.get_priority_PV(), expected_alarm)

    @parameterized.expand(get_status_labels())
    def test_GIVEN_turbo_status_WHEN_turbo_status_read_THEN_turbo_status_read_back(self, turbo_status, IOC_status_label, expected_alarm):
        # GIVEN
        self._lewis.backdoor_run_function_on_device(self.get_status_setter(), arguments=(turbo_status, ))

        # THEN
        self.ca.assert_that_pv_is(self.get_base_PV(), IOC_status_label)
        self.ca.assert_that_pv_alarm_is(self.get_base_PV(), expected_alarm)

    def test_GIVEN_device_disconnected_WHEN_base_PV_read_THEN_alert_and_priority_PVs_read_disconnected(self):
        # GIVEN
        self._lewis.backdoor_set_on_device("is_connected", False)

        expected_alarm = ChannelAccess.Alarms.INVALID

        # THEN
        self.ca.assert_that_pv_alarm_is(self.get_base_PV(), expected_alarm)
        self.ca.assert_that_pv_alarm_is(self.get_alert_PV(), expected_alarm)
        self.ca.assert_that_pv_alarm_is(self.get_priority_PV(), expected_alarm)


@six.add_metaclass(ABCMeta)
class GaugeTestBase(EdwardsTICBase):

    @abstractmethod
    def get_gauge_number(self):
        pass

    def get_base_PV(self):
        return "GAUGE{}:STA".format(self.get_gauge_number())

    def get_alert_PV(self):
        return "GAUGE{}:ALERT".format(self.get_gauge_number())

    def get_priority_PV(self):
        return "GAUGE{}:PRI".format(self.get_gauge_number())

    def get_status_setter(self):
        return "set_gauge_state"

    def get_alert_function(self):
        return "set_gauge_alert"

    def get_priority_function(self):
        return "set_gauge_priority"

    def get_status_labels():
        return [("status", "Status", ChannelAccess.Alarms.NONE),
                ("not_connected", "Not Connected", ChannelAccess.Alarms.NONE),
                ("connected", "Connected", ChannelAccess.Alarms.NONE),
                ("new_id", "New ID", ChannelAccess.Alarms.NONE),
                ("change", "Change", ChannelAccess.Alarms.NONE),
                ("alert", "Alert", ChannelAccess.Alarms.NONE),
                ("off", "Off", ChannelAccess.Alarms.NONE),
                ("striking", "Striking", ChannelAccess.Alarms.NONE),
                ("calibrating", "Calibrating", ChannelAccess.Alarms.NONE),
                ("zeroing", "Zeroing", ChannelAccess.Alarms.NONE),
                ("degassing", "Degassing", ChannelAccess.Alarms.NONE),
                ("on", "On", ChannelAccess.Alarms.NONE),
                ("inhibited", "Inhibited", ChannelAccess.Alarms.NONE)]

    @parameterized.expand([
        ("0", 0),
        ("-1", -1),
        ("1", 1),
        ("1.23", 1.23),
        ("12.3", 12.3)
        ])
    def test_GIVEN_gauge_pressure_WHEN_gauge_status_requested_THEN_gauge_pressure_read_back(self, _, pressure_to_test):
        # GIVEN
        self._lewis.backdoor_set_on_device("gauge_pressure", pressure_to_test)

        # THEN
        self.ca.assert_that_pv_is_number("GAUGE{}:PRESSURE".format(self.get_gauge_number()),
                                         pressure_to_test,
                                         tolerance=0.1*abs(pressure_to_test))

    @parameterized.expand([
        ("Pa", "Pa"),
        ("V", "V"),
        ("percent", "%")
        ])
    def test_GIVEN_gauge_units_WHEN_gauge_status_requested_THEN_correct_units_read_back(self, unit, unit_label):
        # GIVEN
        self._lewis.backdoor_run_function_on_device("set_gauge_units", arguments=(unit, ))

        # THEN
        self.ca.assert_that_pv_is("GAUGE{}:UNIT".format(self.get_gauge_number()), unit_label)
        self.ca.assert_that_pv_is("GAUGE{}:PRESSURE.EGU".format(self.get_gauge_number()), unit_label)

    def test_THAT_gauge_visibility_PV_exists(self):
        # The gauge visibility PV will always be YES in the tests, as they boot 'using' all of the gauges. 
        self.ca.assert_that_pv_is("GAUGE{}VISIBLE".format(self.get_gauge_number()), "YES")


class EdwardsTICTests(unittest.TestCase):
    """
    Tests for the Edwards Turbo Instrument Controller (TIC) IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("edwardstic", DEVICE_PREFIX)

        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("is_connected", True)

        self.ca.assert_setting_setpoint_sets_readback("No", "TURBO:STBY", set_point_pv="TURBO:SETSTBY", timeout=30)

    def test_GIVEN_turbo_pump_switched_on_WHEN_status_requested_THEN_status_reads_switched_on(self):
        # GIVEN
        self.ca.set_pv_value("TURBO:START", "On", wait=True)

        # THEN
        self.ca.assert_that_pv_is("TURBO:STA", "Running")

    def test_GIVEN_standby_mode_switched_on_WHEN_status_requested_THEN_standby_reads_switched_on(self):
        # GIVEN
        self.ca.set_pv_value("TURBO:SETSTBY", "Yes", wait=True)

        # THEN
        self.ca.assert_that_pv_is("TURBO:STBY", "Yes")

    def test_GIVEN_standby_mode_switched_off_WHEN_status_requested_THEN_standby_reads_switched_off(self):
        # GIVEN
        self.ca.set_pv_value("TURBO:SETSTBY", "No", wait=True)

        # THEN
        self.ca.assert_that_pv_is("TURBO:STBY", "No")

    @parameterized.expand([
        ("turbo_status", "TURBO:STA"),
        ("turbo_speed", "TURBO:SPEED"),
        ("turbo_power", "TURBO:POWER"),
        ("turbo_norm", "TURBO:NORM"),
        ("turbo_standby", "TURBO:STBY"),
        ("turbo_cycle", "TURBO:CYCLE")
    ])
    def test_GIVEN_disconnected_device_THEN_record_redirected_PVs_read_invalid(self, _, base_pv):
        # GIVEN
        self._lewis.backdoor_set_on_device("is_connected", False)

        # WHEN
        self.ca.assert_that_pv_alarm_is(base_pv, self.ca.Alarms.INVALID, timeout=20)
        self.ca.assert_that_pv_alarm_is("{base}:ALERT".format(base=base_pv), self.ca.Alarms.INVALID)
        self.ca.assert_that_pv_alarm_is("{base}:PRI".format(base=base_pv), self.ca.Alarms.INVALID)


class TurboStatusTests(EdwardsTICBase, unittest.TestCase):
    def get_base_PV(self):
        return "TURBO:STA"

    def get_alert_PV(self):
        return "TURBO:STA:ALERT"

    def get_priority_PV(self):
        return "TURBO:STA:PRI"

    def get_status_setter(self):
        return "set_turbo_pump_state"

    def get_alert_function(self):
        return "set_turbo_alert"

    def get_priority_function(self):
        return "set_turbo_priority"

    def get_status_labels():
        return [("stopped", "Stopped", ChannelAccess.Alarms.NONE),
                ("starting_delay", "Starting Delay", ChannelAccess.Alarms.NONE),
                ("accelerating", "Accelerating", ChannelAccess.Alarms.NONE),
                ("running", "Running", ChannelAccess.Alarms.NONE),
                ("stopping_short_delay", "Stopping Short Delay", ChannelAccess.Alarms.NONE),
                ("stopping_normal_delay", "Stopping Normal Delay", ChannelAccess.Alarms.NONE),
                ("fault_braking", "Fault Breaking", ChannelAccess.Alarms.MAJOR),
                ("braking", "Braking", ChannelAccess.Alarms.NONE)]


class Gauge1Tests(GaugeTestBase, unittest.TestCase):
    def get_gauge_number(self):
        return 1


class Gauge2Tests(GaugeTestBase, unittest.TestCase):
    def get_gauge_number(self):
        return 2


class Gauge3Tests(GaugeTestBase, unittest.TestCase):
    def get_gauge_number(self):
        return 3
