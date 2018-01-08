class DeviceLauncher(object):
    """
    Launches an IOC and associated emulator
    """

    def __init__(self, ioc, lewis):
        self.ioc = ioc
        self.lewis = lewis

    def __enter__(self):
        self.ioc.__enter__()
        if self.lewis is not None:
            self.lewis.__enter__()

    def __exit__(self, *args, **kwargs):
        self.ioc.__exit__(*args, **kwargs)
        if self.lewis is not None:
            self.lewis.__exit__(*args, **kwargs)


class DeviceCollectionLauncher(object):
    """
    Launches a collection of devices (device = ioc + emulator)
    """
    def __init__(self, devices):
        self.devices = devices

    def __enter__(self):
        for device in self.devices:
            device.__enter__()

    def __exit__(self, *args, **kwargs):
        for device in self.devices:
            device.__exit__(*args, **kwargs)

    def __iter__(self):
        return iter(self.devices)
