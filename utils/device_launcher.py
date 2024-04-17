from contextlib import contextmanager
try:
    from contextlib import ExitStack  # PY3
except ImportError:
    from contextlib2 import ExitStack  # PY2


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
    try:
        with ExitStack() as stack:
            for device in devices:
                stack.enter_context(device)
            yield
    except GeneratorExit:
        print("Cleaning up... please wait")
        raise
