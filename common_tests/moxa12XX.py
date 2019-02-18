from __future__ import division
import six

from abc import ABCMeta, abstractmethod

from utils.channel_access import ChannelAccess
from utils.testing import get_running_lewis_and_ioc
from itertools import product


@six.add_metaclass(ABCMeta)
class Moxa12XXBase(object):
    """
    Tests for a moxa ioLogik e1240. (8x DC Voltage/Current measurements)
    """

    @abstractmethod
    def get_device_prefix(self):
        pass

    @abstractmethod
    def get_PV_name(self):
        pass

    @abstractmethod
    def get_number_of_channels(self):
        pass

    @abstractmethod
    def get_setter_function_name(self):
        pass

    @abstractmethod
    def get_starting_reg_addr(self):
        pass

    @abstractmethod
    def get_test_values(self):
        pass

    @abstractmethod
    def get_raw_ir_setter(self):
        pass

    @abstractmethod
    def get_raw_ir_pv(self):
        pass

    @abstractmethod
    def get_alarm_limits(self):
        pass

    @abstractmethod
    def get_registers_per_channel(self):
        pass

    @abstractmethod
    def get_channel_format(self):
        pass

    def setUp(self):

        self.NUMBER_OF_CHANNELS = self.get_number_of_channels()

        self.CHANNELS = range(self.NUMBER_OF_CHANNELS)

        self.low_alarm_limit, self.high_alarm_limit = self.get_alarm_limits()

        self._lewis, self._ioc = get_running_lewis_and_ioc("moxa12xx", self.get_device_prefix())

        self.ca = ChannelAccess(device_prefix=self.get_device_prefix())

        # Sends a backdoor command to the device to reset all input registers (IRs) to 0
        reset_value = 0
        self._lewis.backdoor_run_function_on_device("set_ir", (self.get_starting_reg_addr(),
                                                               [reset_value]*self.get_registers_per_channel()*self.NUMBER_OF_CHANNELS))

    def test_WHEN_an_AI_input_is_changed_THEN_that_channel_readback_updates(self):
        for channel, test_value in product(self.CHANNELS, self.get_test_values()):
            register_offset = channel * self.get_registers_per_channel()

            self._lewis.backdoor_run_function_on_device(self.get_setter_function_name(),
                                                        (self.get_starting_reg_addr() + register_offset, test_value))

            self.ca.assert_that_pv_is_number("CH{:01d}:{PV}".format(channel, PV=self.get_PV_name()),
                                             test_value, tolerance=0.1*abs(test_value))

    def test_WHEN_device_voltage_is_below_low_limit_THEN_PV_shows_major_alarm(self):
        for channel in range(self.get_number_of_channels()):
            register_offset = channel * self.get_registers_per_channel()

            valid_value = 0.5*(self.low_alarm_limit + self.high_alarm_limit)

            self._lewis.backdoor_run_function_on_device(self.get_setter_function_name(),
                                                        (self.get_starting_reg_addr() + register_offset, valid_value))

            self.ca.assert_that_pv_is_number("CH{:01d}:{PV}".format(channel, PV=self.get_PV_name()),
                                             valid_value, tolerance=0.1*valid_value)

            self.ca.assert_that_pv_alarm_is("CH{:01d}:{PV}".format(channel, PV=self.get_PV_name()), self.ca.Alarms.NONE)

            value_to_set = self.low_alarm_limit - 1.0

            self._lewis.backdoor_run_function_on_device(self.get_setter_function_name(),
                                                        (self.get_starting_reg_addr() + register_offset, value_to_set))

            self.ca.assert_that_pv_is_number("CH{:01d}:{PV}".format(channel, PV=self.get_PV_name()),
                                             value_to_set, tolerance=0.1*value_to_set)

            self.ca.assert_that_pv_alarm_is("CH{:01d}:{PV}".format(channel, PV=self.get_PV_name()),
                                            self.ca.Alarms.MAJOR)

    def test_WHEN_device_voltage_is_above_high_limit_THEN_PV_shows_major_alarm(self):
        for channel in range(self.get_number_of_channels()):
            register_offset = channel * self.get_registers_per_channel()

            valid_value = 0.5*(self.low_alarm_limit + self.high_alarm_limit)

            self._lewis.backdoor_run_function_on_device(self.get_setter_function_name(),
                                                        (self.get_starting_reg_addr() + register_offset, valid_value))

            self.ca.assert_that_pv_alarm_is("CH{:01d}:{PV}".format(channel, PV=self.get_PV_name()), self.ca.Alarms.NONE)

            value_to_set = self.high_alarm_limit + 1.0

            self._lewis.backdoor_run_function_on_device(self.get_setter_function_name(),
                                                        (self.get_starting_reg_addr() + register_offset, value_to_set))

            self.ca.assert_that_pv_alarm_is("CH{:01d}:{PV}".format(channel, PV=self.get_PV_name()),
                                            self.ca.Alarms.MAJOR)

    def test_WHEN_a_channel_is_aliased_THEN_a_PV_with_that_alias_exists(self):
        for channel in range(self.get_number_of_channels()):
            self.ca.assert_that_pv_exists(self.get_channel_format().format(channel))
