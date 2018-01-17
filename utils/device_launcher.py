from contextlib import contextmanager
import sys

from ioc_launcher import IOCRegister


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
    launched_devices = []
    try:
        for device in devices:
            device.__enter__()
            launched_devices.append(device)

        yield
    finally:
        for device in reversed(launched_devices):
            device.__exit__(*sys.exc_info())
