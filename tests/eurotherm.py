import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

# Internal Address of device (must be 2 characters)
ADDRESS = "01"

# MACROS to use for the IOC
MACROS = {"ADDR": ADDRESS}


class EurothermTests(unittest.TestCase):
    """
    Tests for the Eurotherm temperature controller.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("eurotherm")

        self.ca = ChannelAccess()
        self.ca.wait_for("AMINT2L_01:PRESSURE", timeout=30)
        self._lewis.backdoor_set_on_device("address", ADDRESS)

