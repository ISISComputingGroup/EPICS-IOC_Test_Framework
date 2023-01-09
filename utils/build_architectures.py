"""
Possible build configs
"""
from enum import Enum


class BuildArchitectures(Enum):
    """
    Build configuration types with which a set of unit tests can be run.
    """
    _64BIT = 1
    _32BIT = 2

    @staticmethod
    def archname(arch):
        """
        Returns: nice name of architecture
        """
        if arch == BuildArchitectures._64BIT:
            return "64 bit"
        elif arch == BuildArchitectures._32BIT:
            return "32 bit"
        elif arch is None:
            return "test build archs not set!!!!"
        else:
            return "Unknown"
