"""
Formatters for data.
"""


def format_value(value):
    """
    Formats a value for display. Includes type information to ease debugging.

    Args:
        value: The value to format.
    Returns:
        string: The formatted value.
    """
    return "'{}' (type: '{}')".format(value, value.__class__.__name__)
