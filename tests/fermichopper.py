import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

import math


class FermichopperTests(unittest.TestCase):
    """
    Tests for the Fermi Chopper IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("fermichopper")

        self.ca = ChannelAccess(15)
        self.ca.wait_for("FERMCHOP_01:DISABLE", timeout=30)

    def test_WHEN_ioc_is_started_THEN_ioc_is_not_disabled(self):
        self.ca.assert_that_pv_is("FERMCHOP_01:DISABLE", "COMMS ENABLED")
