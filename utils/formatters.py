"""
Formatters for data.
"""

from typing import Any


def format_value(value: Any) -> str:  # noqa: ANN401
    """
    Formats a value for display. Includes type information to ease debugging.

    Args:
        value: The value to format.
    Returns:
        string: The formatted value.
    """
    return f"'{value}' (type: '{value.__class__.__name__}')"
