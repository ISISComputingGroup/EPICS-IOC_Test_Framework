import unittest
from utils.channel_access import ChannelAccess


TOO_HIGH_PID_VALUE = 100000
TOO_LOW_PID_VALUE = -100000


class JulaboTests(unittest.TestCase):
    """
    Tests for the Julabo IOC.
    """

    def setUp(self):
        self.ca = ChannelAccess()
        # Turn off circulate
        self.ca.set_pv_value("JULABO_01:MODE:SP", 0)

    def test_set_new_temperature_sets_setpoint_readback_correctly(self):
        # Get current temp
        start_t = self.ca.get_pv_value("JULABO_01:TEMP")
        # Set new temp via SP
        self.ca.set_pv_value("JULABO_01:TEMP:SP", start_t + 5)
        # Check SP RBV matches new temp
        self.assertEqual(start_t + 5, self.ca.get_pv_value("JULABO_01:TEMP:SP:RBV"))

    def test_setting_temperature_above_high_limit_does_not_set_value(self):
        # Get current temp sp rbv
        start_t = self.ca.get_pv_value("JULABO_01:TEMP:SP:RBV")
        # Get high limit
        high_t = self.ca.get_pv_value("JULABO_01:HIGHLIMIT")
        # Set new temp to above high limit
        self.ca.set_pv_value("JULABO_01:TEMP:SP", high_t + 5)
        # Check SP RBV hasn't changed
        self.assertEqual(start_t, self.ca.get_pv_value("JULABO_01:TEMP:SP:RBV"))

    def test_setting_temperature_below_low_limit_does_not_set_value(self):
        # Get current temp sp rbv
        start_t = self.ca.get_pv_value("JULABO_01:TEMP:SP:RBV")
        # Get low limit
        low_t = self.ca.get_pv_value("JULABO_01:LOWLIMIT")
        # Set new temp to above high limit
        self.ca.set_pv_value("JULABO_01:TEMP:SP", low_t - 5)
        # Check SP RBV hasn't changed
        self.assertEqual(start_t, self.ca.get_pv_value("JULABO_01:TEMP:SP:RBV"))

    def test_set_new_temperature_with_circulate_off_means_temperature_remains_unchanged(self):
        # Get current temp
        start_t = self.ca.get_pv_value("JULABO_01:TEMP")
        # Set new temp via SP
        self.ca.set_pv_value("JULABO_01:TEMP:SP", start_t + 5)
        # Check temp hasn't changed
        self.assertEqual(start_t, self.ca.get_pv_value("JULABO_01:TEMP"))

    def test_set_new_temperature_with_circulate_on_changes_temperature(self):
        # Get current temp plus a bit
        start_t = self.ca.get_pv_value("JULABO_01:TEMP") + 1
        # Set new temp via SP
        self.ca.set_pv_value("JULABO_01:TEMP:SP", start_t)
        # Turn on circulate
        self.ca.set_pv_value("JULABO_01:MODE:SP", 1)
        # Check temp has changed
        self.assertEqual(start_t, self.ca.get_pv_value("JULABO_01:TEMP"))

    def test_setting_external_PID_sets_values_correctly(self):
        # Get initial values and add to them
        p = self.ca.get_pv_value("JULABO_01:EXTP") + 1
        i = self.ca.get_pv_value("JULABO_01:EXTI") + 1
        d = self.ca.get_pv_value("JULABO_01:EXTD") + 1
        # Set new values
        self.ca.set_pv_value("JULABO_01:EXTP:SP", p)
        self.ca.set_pv_value("JULABO_01:EXTI:SP", i)
        self.ca.set_pv_value("JULABO_01:EXTD:SP", d)
        # Check values have changed
        self.assertEqual(p, self.ca.get_pv_value("JULABO_01:EXTP"))
        self.assertEqual(i, self.ca.get_pv_value("JULABO_01:EXTI"))
        self.assertEqual(d, self.ca.get_pv_value("JULABO_01:EXTD"))

    def test_setting_internal_PID_sets_values_correctly(self):
        # Get initial values and add to them
        p = self.ca.get_pv_value("JULABO_01:INTP") + 1
        i = self.ca.get_pv_value("JULABO_01:INTI") + 1
        d = self.ca.get_pv_value("JULABO_01:INTD") + 1
        # Set new values
        self.ca.set_pv_value("JULABO_01:INTP:SP", p)
        self.ca.set_pv_value("JULABO_01:INTI:SP", i)
        self.ca.set_pv_value("JULABO_01:INTD:SP", d)
        # Check values have changed
        self.assertEqual(p, self.ca.get_pv_value("JULABO_01:INTP"))
        self.assertEqual(i, self.ca.get_pv_value("JULABO_01:INTI"))
        self.assertEqual(d, self.ca.get_pv_value("JULABO_01:INTD"))

    def test_setting_internal_PID_above_limit_does_nothing(self):
        # Get initial values
        start_p = self.ca.get_pv_value("JULABO_01:INTP")
        start_i = self.ca.get_pv_value("JULABO_01:INTI")
        start_d = self.ca.get_pv_value("JULABO_01:INTD")
        # Set outside of range
        self.ca.set_pv_value("JULABO_01:INTP:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:INTI:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:INTD:SP", TOO_HIGH_PID_VALUE)
        # Check values have not changed
        self.assertEqual(start_p, self.ca.get_pv_value("JULABO_01:INTP"))
        self.assertEqual(start_i, self.ca.get_pv_value("JULABO_01:INTI"))
        self.assertEqual(start_d, self.ca.get_pv_value("JULABO_01:INTD"))

    def test_setting_internal_PID_below_limit_does_nothing(self):
        # Get initial values
        start_p = self.ca.get_pv_value("JULABO_01:INTP")
        start_i = self.ca.get_pv_value("JULABO_01:INTI")
        start_d = self.ca.get_pv_value("JULABO_01:INTD")
        # Set outside of range
        self.ca.set_pv_value("JULABO_01:INTP:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:INTI:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:INTD:SP", TOO_LOW_PID_VALUE)
        # Check values have not changed
        self.assertEqual(start_p, self.ca.get_pv_value("JULABO_01:INTP"))
        self.assertEqual(start_i, self.ca.get_pv_value("JULABO_01:INTI"))
        self.assertEqual(start_d, self.ca.get_pv_value("JULABO_01:INTD"))

    def test_setting_external_PID_above_limit_does_nothing(self):
        # Get initial values
        start_p = self.ca.get_pv_value("JULABO_01:EXTP")
        start_i = self.ca.get_pv_value("JULABO_01:EXTI")
        start_d = self.ca.get_pv_value("JULABO_01:EXTD")
        # Set outside of range
        self.ca.set_pv_value("JULABO_01:EXTP:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:EXTI:SP", TOO_HIGH_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:EXTD:SP", TOO_HIGH_PID_VALUE)
        # Check values have not changed
        self.assertEqual(start_p, self.ca.get_pv_value("JULABO_01:EXTP"))
        self.assertEqual(start_i, self.ca.get_pv_value("JULABO_01:EXTI"))
        self.assertEqual(start_d, self.ca.get_pv_value("JULABO_01:EXTD"))

    def test_setting_external_PID_below_limit_does_nothing(self):
        # Get initial values
        start_p = self.ca.get_pv_value("JULABO_01:EXTP")
        start_i = self.ca.get_pv_value("JULABO_01:EXTI")
        start_d = self.ca.get_pv_value("JULABO_01:EXTD")
        # Set outside of range
        self.ca.set_pv_value("JULABO_01:EXTP:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:EXTI:SP", TOO_LOW_PID_VALUE)
        self.ca.set_pv_value("JULABO_01:EXTD:SP", TOO_LOW_PID_VALUE)
        # Check values have not changed
        self.assertEqual(start_p, self.ca.get_pv_value("JULABO_01:EXTP"))
        self.assertEqual(start_i, self.ca.get_pv_value("JULABO_01:EXTI"))
        self.assertEqual(start_d, self.ca.get_pv_value("JULABO_01:EXTD"))