import os
import imp
import importlib
import unittest
import time
import xmlrunner
import argparse
from contextlib import contextmanager
from utils.lewis_launcher import LewisLauncher, LewisNone
from utils.ioc_launcher import IocLauncher, IOCRegister
from utils.free_ports import get_free_ports


def package_contents(package_name):
    """
    Finds all the modules in a package.

    :param package_name: the name of the package
    :return: a set containing all the module names
    """
    filename, pathname, description = imp.find_module(package_name)
    if filename:
        raise ImportError('Not a package: %r', package_name)
    # Use a set because some may be both source and compiled.
    return set([os.path.splitext(module)[0] for module in os.listdir(pathname)
                if module.endswith('.py') and not module.startswith("__init__")])


def load_module(name):
    """
    Loads a module based on its name.

    :param name: the name of the module
    :return: a reference to the module
    """
    return importlib.import_module(name, )


@contextmanager
def modified_environment(**kwargs):
    """
    Modifies the environment variables as required then returns them to their original state.

    :param kwargs: the settings to apply
    """
    # Copying old values
    old_env = {name: os.environ.get(name, '') for name in kwargs.keys()}

    # Apply new settings and then yield
    os.environ.update(kwargs)
    yield

    # Restore old values
    os.environ.update(old_env)


def run_test(prefix, device, ioc_launcher, lewis_launcher):
    """
    Runs the tests for the specified IOC.

    :param prefix: the instrument prefix
    :param device: the name of the IOC type
    :param ioc_launcher: the ioc launcher
    :param lewis_launcher: the lewis simulator to use; To not use use the LewisNone object
    """
    # Define an environment variable with the prefix in it
    # This can then be accessed elsewhere
    os.environ["testing_prefix"] = prefix

    # Load the device's test module and get the class
    m = load_module('tests.%s' % device.lower())

    test_class = getattr(m, "%sTests" % device.capitalize())

    port = str(get_free_ports(1)[0])
    lewis_launcher.port = port
    ioc_launcher.port = port
    try:
        ioc_launcher.macros = m.MACROS
    except AttributeError:
        ioc_launcher.macros = {}

    settings = dict()
    # Need to set epics address list to local broadcast otherwise channel access won't work
    settings['EPICS_CA_ADDR_LIST'] = "127.255.255.255"

    with modified_environment(**settings):
        with lewis_launcher:
            with ioc_launcher:
                if not lewis_launcher.check():
                    exit(-1)
#                runner = unittest.TextTestRunner()
                runner = xmlrunner.XMLTestRunner(output='test-reports')
                test_suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                runner.run(test_suite)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Test an IOC under emulation by running tests against it')
    parser.add_argument('-l', '--list-devices', help="List available devices for testing.", action="store_true")
    parser.add_argument('-pf', '--prefix', default=None, help='The instrument prefix; e.g. TE:NDW1373')
    parser.add_argument('-d', '--device', default=None, help="Device type to test.")
    parser.add_argument('-p', '--ioc-path', default=None, help="The path to the folder containing the IOC's st.cmd")
    parser.add_argument('-e', '--emulator-path', default=None, help="The path of the lewis.py file")
    parser.add_argument('-py', '--python-path', default="C:\Instrument\Apps\Python\python.exe", help="The path of python.exe")
    parser.add_argument('-ep', '--emulator-protocol', default=None, help="The Lewis protocal to use (optional)")
    parser.add_argument('-r', '--record-simulation', default=False, action="count",
                        help="Use record simulation rather than emulation (optional)")
    parser.add_argument('-ea', '--emulator-add-path', default=None, help="Add path where device packages exist for the emulator.")
    parser.add_argument('-ek', '--emulator-device-package', default=None, help="Name of packages where devices are found.")

    parser.add_argument('--var-dir', default=None, help="Directory in which to create a log dir to write log file to and "
                                                        "directory in which to create tmp dir which contains environments "
                                                        "variables for the IOC. Defaults to environment variable ICPVARDIR and current dir if empty.")

    arguments = parser.parse_args()

    if arguments.list_devices:
        print("Available tests:")
        print('\n'.join(package_contents("tests")))
        exit(0)
    else:
        if arguments.var_dir is None:
            var_dir = os.getenv("ICPVARDIR", os.curdir)
        else:
            var_dir = arguments.var_dir

        if arguments.prefix is None:
            print("Cannot run without instrument prefix")
            exit(-1)
        elif arguments.record_simulation >= 1 and arguments.device and arguments.ioc_path:
            print("Running using record simulation")
            lewis = LewisNone(arguments.device)
            iocLauncher = IocLauncher(
                device=arguments.device,
                directory=os.path.abspath(arguments.ioc_path),
                use_rec_sim=True,
                var_dir=var_dir)
            run_test(arguments.prefix, arguments.device, iocLauncher, lewis)
        elif arguments.device and arguments.ioc_path and arguments.emulator_path:
            print("Running using device emulation")
            lewis = LewisLauncher(
                device=arguments.device,
                python_path=os.path.abspath(arguments.python_path),
                lewis_path=os.path.abspath(arguments.emulator_path),
                lewis_protocol=arguments.emulator_protocol,
                lewis_additional_path=arguments.emulator_add_path,
                lewis_package=arguments.emulator_device_package,
                var_dir=var_dir)
            iocLauncher = IocLauncher(
                device=arguments.device,
                directory=os.path.abspath(arguments.ioc_path),
                use_rec_sim=False,
                var_dir=var_dir)
            run_test(arguments.prefix, arguments.device, iocLauncher, lewis)
        else:
            print("Type -h for help")
            exit(-1)
