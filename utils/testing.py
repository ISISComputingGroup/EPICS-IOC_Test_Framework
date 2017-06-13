from utils.ioc_launcher import IOCRegister, IocLauncher
from utils.lewis_launcher import LewisRegister, LewisLauncher


def get_running_lewis_and_ioc(device_name):
    """
    Assert that the emulator and ioc have been started if needed.

    :param device_name: the device name
    :return: lewis launcher and ioc launcher tuple
    :rtype: (LewisLauncher, IocLauncher)
    """
    lewis = LewisRegister.get_running(device_name)
    ioc = IOCRegister.get_running(device_name)

    if ioc is None and lewis is None:
        raise AssertionError("Emulator and IOC for {device} are not running".format(device=device_name))
    if ioc is None:
        raise AssertionError("IOC for {device} is not running".format(device=device_name))
    if lewis is None:
        raise AssertionError("Emulator for {device} is not running".format(device=device_name))

    return lewis, ioc
