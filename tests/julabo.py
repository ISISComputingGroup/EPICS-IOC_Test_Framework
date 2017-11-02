import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

TOO_HIGH_PID_VALUE = 100000
TOO_LOW_PID_VALUE = -100000


class JulaboTests(unittest.TestCase):
    """
    Tests for the Julabo IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("julabo")
        self.ca = ChannelAccess(device_prefix="JULABO_01")
        self.ca.wait_for("TEMP", timeout=30)
        # Turn off circulate
        self.ca.set_pv_value("MODE:SP", "OFF")

    def test_set_new_temperature_sets_setpoint_readback_correctly(self):
        # Get current temp
        start_t = self.ca.get_pv_value("TEMP")
        # Set new temp via SP
        self.ca.set_pv_value("TEMP:SP", start_t + 5)
        # Check SP RBV matches new temp
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", start_t + 5)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_setting_temperature_above_high_limit_does_not_set_value(self):
        # Get current temp sp rbv
        start_t = self.ca.get_pv_value("TEMP:SP:RBV")
        # Get high limit
        high_t = self.ca.get_pv_value("HIGHLIMIT")
        # Set new temp to above high limit
        self.ca.set_pv_value("TEMP:SP", high_t + 5)
        # Check SP RBV hasn't changed
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", start_t)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_setting_temperature_below_low_limit_does_not_set_value(self):
        # Get current temp sp rbv
        start_t = self.ca.get_pv_value("TEMP:SP:RBV")
        # Get low limit
        low_t = self.ca.get_pv_value("LOWLIMIT")
        # Set new temp to above high limit
        self.ca.set_pv_value("TEMP:SP", low_t - 5)
        # Check SP RBV hasn't changed
        self.ca.assert_that_pv_is_number("TEMP:SP:RBV", start_t)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_set_new_temperature_with_circulate_off_means_temperature_remains_unchanged(self):
        # Get current temp
        start_t = self.ca.get_pv_value("TEMP")
        # Set new temp via SP
        self.ca.set_pv_value("TEMP:SP", start_t + 5)
        # Check temp hasn't changed
        self.ca.assert_that_pv_is_number("TEMP", start_t)

    def test_set_new_temperature_with_circulate_on_changes_temperature(self):
        # Get current temp plus a bit
        new_t = self.ca.get_pv_value("TEMP") + 1
        # Set new temp via SP
        self.ca.set_pv_value("TEMP:SP", new_t)
        # Turn on circulate
        self.ca.set_pv_value("MODE:SP", "ON")
        # Check temp has changed
        self.ca.assert_that_pv_is_number("TEMP", new_t, timeout=10)

    def test_setting_external_PID_sets_values_correctly(self):
        # Get initial values and add to them
        p = self.ca.get_pv_value("EXTP") + 1
        i = self.ca.get_pv_value("EXTI") + 1
        d = self.ca.get_pv_value("EXTD") + 1
        # Set new values
        self.ca.set_pv_value("EXTP:SP", p)
        self.ca.set_pv_value("EXTI:SP", i)
        self.ca.set_pv_value("EXTD:SP", d)
        # Check values have changed
        self.ca.assert_that_pv_is_number("EXTP", p)
        self.ca.assert_that_pv_is_number("EXTI", i)
        self.ca.assert_that_pv_is_number("EXTD", d)

    def test_setting_internal_PID_sets_values_correctly(self):
        # Get initial values and add to them
        p = self.ca.get_pv_value("INTP") + 1
        i = self.ca.get_pv_value("INTI") + 1
        d = self.ca.get_pv_value("INTD") + 1
        # Set new values
        self.ca.set_pv_value("INTP:SP", p)
        self.ca.set_pv_value("INTI:SP", i)
        self.ca.set_pv_value("INTD:SP", d)
        # Check values have changed
        self.ca.assert_that_pv_is_number("INTP", p)
        self.ca.assert_that_pv_is_number("INTI", i)
        self.ca.assert_that_pv_is_number("INTD", d)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_setting_internal_PID_above_limit_does_nothing(self):
        # Get initial values
        p = self.ca.get_pv_value("INTP")
        i = self.ca.get_pv_value("INTI")
        d = self.ca.get_pv_value("INTD")
        # Set outside of range
        self.ca.set_pv_value("INTP:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("INTI:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("INTD:SP", TOO_HIGH_PID_VALUE)
        # Check values have not changed
        self.ca.assert_that_pv_is_number("INTP", p)
        self.ca.assert_that_pv_is_number("INTI", i)
        self.ca.assert_that_pv_is_number("INTD", d)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_setting_internal_PID_below_limit_does_nothing(self):
        # Get initial values
        p = self.ca.get_pv_value("INTP")
        i = self.ca.get_pv_value("INTI")
        d = self.ca.get_pv_value("INTD")
        # Set outside of range
        self.ca.set_pv_value("INTP:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("INTI:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("INTD:SP", TOO_LOW_PID_VALUE)
        # Check values have not changed
        self.ca.assert_that_pv_is_number("INTP", p)
        self.ca.assert_that_pv_is_number("INTI", i)
        self.ca.assert_that_pv_is_number("INTD", d)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_setting_external_PID_above_limit_does_nothing(self):
        # Get initial values
        p = self.ca.get_pv_value("EXTP")
        i = self.ca.get_pv_value("EXTI")
        d = self.ca.get_pv_value("EXTD")
        # Set outside of range
        self.ca.set_pv_value("EXTP:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("EXTI:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("EXTD:SP", TOO_HIGH_PID_VALUE)
        # Check values have not changed
        self.ca.assert_that_pv_is_number("EXTP", p)
        self.ca.assert_that_pv_is_number("EXTI", i)
        self.ca.assert_that_pv_is_number("EXTD", d)

    @skipIf(IOCRegister.uses_rec_sim, "In rec sim this test fails")
    def test_setting_external_PID_below_limit_does_nothing(self):
        # Get initial values
        p = self.ca.get_pv_value("EXTP")
        i = self.ca.get_pv_value("EXTI")
        d = self.ca.get_pv_value("EXTD")
        # Set outside of range
        self.ca.set_pv_value("EXTP:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("EXTI:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("EXTD:SP", TOO_LOW_PID_VALUE)
        # Check values have not changed
        self.ca.assert_that_pv_is_number("EXTP", p)
        self.ca.assert_that_pv_is_number("EXTI", i)
        self.ca.assert_that_pv_is_number("EXTD", d)
