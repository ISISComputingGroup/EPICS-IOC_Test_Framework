import abc

from parameterized import parameterized

from utils.testing import skip_if_recsim


class TtiCommon(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_off_state_name(self):
        pass

    @abc.abstractmethod
    def get_on_state_name(self):
        pass

    @parameterized.expand([[0], [1], [2]])
    def test_WHEN_voltage_is_set_THEN_voltage_setpoint_updates(self, volt):
        self.ca.set_pv_value("VOLTAGE:SP", volt)
        self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", volt)

    @parameterized.expand([[0.01], [1.30], [5.0]])
    def test_WHEN_current_setpoint_is_set_THEN_current_readback_updates(self, current):
        self.ca.set_pv_value("CURRENT:SP", current)
        self.ca.assert_that_pv_is("CURRENT:SP:RBV", current)

    def test_WHEN_outputstatus_is_set_THEN_outputstatus_readback_updates(self):
        for status in [self.get_on_state_name(), self.get_off_state_name()]:
            self.ca.set_pv_value("OUTPUTSTATUS:SP", status)
            self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", status)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_ioc_not_in_error_state_THEN_correct_error_state_returned(self):
        expected_value = "No error"
        self.ca.set_pv_value("CURRENT:SP", 3.0)
        self.ca.assert_that_pv_is("ERROR", expected_value)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_ioc_in_constant_current_mode_THEN_correct_mode_returned(self):
        expected_value = "Constant Current"
        self._lewis.backdoor_set_on_device("output_mode", "M CI")
        self.ca.assert_that_pv_is("OUTPUTMODE", expected_value)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_WHEN_ioc_in_constant_voltage_mode_THEN_correct_mode_returned(self):
        expected_value = "Constant Voltage"
        self._lewis.backdoor_set_on_device("output_mode", "M CV")
        self.ca.assert_that_pv_is("OUTPUTMODE", expected_value)

    @parameterized.expand([[0], [5], [10]])
    def test_GIVEN_set_output_conditions_WHEN_the_output_is_on_THEN_readback_voltage_is_close_to_the_voltage_setpoint(
        self, voltage
    ):
        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", self.get_on_state_name())
        self.ca.set_pv_value("VOLTAGE:SP", voltage)
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", self.get_on_state_name())
        self.ca.assert_that_pv_is("VOLTAGE:SP:RBV", voltage)
        self.ca.assert_that_pv_is_number("VOLTAGE", voltage, tolerance=0.1)

    @parameterized.expand([[0.01], [1.30], [5.0]])
    def test_GIVEN_set_output_conditions_WHEN_the_output_is_on_THEN_readback_current_is_close_to_the_current_setpoint(
        self, current
    ):
        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", self.get_on_state_name())
        self._lewis.backdoor_set_on_device("output_mode", "M CI")
        self.ca.set_pv_value("CURRENT:SP", current)
        self.ca.assert_that_pv_is("CURRENT:SP:RBV", current)
        self.ca.assert_that_pv_is_number("CURRENT", current, tolerance=0.01)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_GIVEN_voltage_WHEN_current_limit_is_lower_than_potential_current_and_output_is_on_THEN_mode_is_CI_and_voltage_is_actual(
        self,
    ):
        expected_voltage = 20
        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self._lewis.backdoor_set_on_device("load_resistance", 8.00)
        self.ca.set_pv_value("CURRENT:SP", 2.5)
        self.ca.set_pv_value("VOLTAGE:SP", 25)
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Current")
        self.ca.assert_that_pv_is("VOLTAGE", expected_voltage)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_GIVEN_voltage_WHEN_current_limit_is_lower_than_potential_current_but_output_off_THEN_mode_is_CV_and_voltage_is_not_actual(
        self,
    ):
        expected_voltage = 0
        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_off_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", self.get_off_state_name())
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self._lewis.backdoor_set_on_device("load_resistance", 8.00)
        self.ca.set_pv_value("CURRENT:SP", 2.5)
        self.ca.set_pv_value("VOLTAGE:SP", 25)
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self.ca.assert_that_pv_is("VOLTAGE", expected_voltage)

    @skip_if_recsim("Behaviour cannot be simulated in Recsim")
    def test_GIVEN_voltage_WHEN_current_limit_is_lower_than_potential_current_but_output_off_THEN_mode_is_CV_and_voltage_is_not_actual_but_close_to_sp(
        self,
    ):
        expected_voltage = 10
        self.ca.set_pv_value("OUTPUTSTATUS:SP", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTSTATUS:SP:RBV", self.get_on_state_name())
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self._lewis.backdoor_set_on_device("load_resistance", 8.00)
        self.ca.set_pv_value("CURRENT:SP", 2.5)
        self.ca.set_pv_value("VOLTAGE:SP", expected_voltage)
        self.ca.assert_that_pv_is("OUTPUTMODE", "Constant Voltage")
        self.ca.assert_that_pv_is_number("VOLTAGE", expected_voltage, tolerance=0.1)
