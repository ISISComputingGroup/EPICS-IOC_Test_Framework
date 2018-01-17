from contextlib import contextmanager
from contextlib2 import ExitStack


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
    with ExitStack() as stack:
        for device in devices:
            stack.enter_context(device)
        yield
