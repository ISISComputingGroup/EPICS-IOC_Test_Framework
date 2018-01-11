from contextlib import contextmanager
import sys


@contextmanager
def device_launcher(ioc, lewis):
    """
    Context manager that launches an ioc and emulator pair
    :param ioc: the ioc launcher
    :param lewis: the lewis launcher
    """
    if lewis is not None:
        with lewis, ioc:
            yield
    else:
        with ioc:
            yield


@contextmanager
def device_collection_launcher(devices):
    """
    Context manager that launches a list of devices
    :param devices: list of context managers representing the devices to launch (see device_launcher above)
    """
    for device in devices:
        device.__enter__()

    try:
        yield
    finally:
        for device in reversed(devices):
            device.__exit__(*sys.exc_info())
