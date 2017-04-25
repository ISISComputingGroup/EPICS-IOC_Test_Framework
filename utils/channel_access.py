import os
import time
from genie_python.genie_cachannel_wrapper import CaChannelWrapper


class ChannelAccess(object):
    """
    Provides the required channel access commands.
    """
    def __init__(self):
        """
        Constructor.
        """
        self.ca = CaChannelWrapper()
        self.prefix = os.environ["testing_prefix"]
        if not self.prefix.endswith(':'):
            self.prefix += ':'

    def set_pv_value(self, pv, value):
        """
        Sets the specified PV to the supplied value.

        :param pv: the EPICS PV name
        :param value: the value to set
        """
        self.ca.set_pv_value(self.prefix + pv, value, wait=True, timeout=5)
        # Need to give Lewis time to process
        time.sleep(1)

    def get_pv_value(self, pv):
        """
        Gets the current value for the specified PV.

        :param pv: the EPICS PV name
        :return: the current value
        """
        return self.ca.get_pv_value(self.prefix + pv)
