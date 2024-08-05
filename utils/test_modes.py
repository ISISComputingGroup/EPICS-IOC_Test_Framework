"""
Possible testsing mmodes
"""

from enum import Enum


class TestModes(Enum):
    """
    Modes in which a set of unit tests can be run
    """

    RECSIM = 1
    DEVSIM = 2
    NOSIM = 3

    @staticmethod
    def name(mode):
        """
        Returns: nice name of mode
        """
        if mode == TestModes.RECSIM:
            return "Rec sim"
        elif mode == TestModes.DEVSIM:
            return "Device sim"
        elif mode == TestModes.NOSIM:
            return "No sim"
        elif mode is None:
            return "test mode not set!!!!"
        else:
            return "Unknown"
