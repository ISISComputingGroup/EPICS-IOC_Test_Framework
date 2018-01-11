import os
import imp
import importlib
import unittest

import sys
import xmlrunner
import argparse
from contextlib import contextmanager

from utils.device_launcher import DeviceLauncher, DeviceCollectionLauncher
from utils.lewis_launcher import LewisLauncher, LewisNone
from utils.ioc_launcher import IocLauncher
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
    module = importlib.import_module(name, )
    return module


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


def run_test(prefix, test_module, device_launchers):
    """
    Runs the tests for the specified IOC.

    :param prefix: the instrument prefix
    :param test_module: the test module
    :param device_launchers: context manager that launches the necessary iocs and associated emulators
    """
    # Define an environment variable with the prefix in it
    # This can then be accessed elsewhere
    os.environ["testing_prefix"] = prefix

    for device_launcher in device_launchers:
        port = str(get_free_ports(1)[0])
        device_launcher.ioc.port = port

        if device_launcher.lewis is not None:
            device_launcher.lewis.port = port

        try:
            device_launcher.ioc.device_prefix = test_module.DEVICE_PREFIX
        except AttributeError:
            device_launcher.ioc.device_prefix = None

        # Override any emulator port that might be set elsewhere
        device_launcher.ioc.macros['EMULATOR_PORT'] = port

    # Need to set epics address list to local broadcast otherwise channel access won't work
    settings = {
        'EPICS_CA_ADDR_LIST': "127.255.255.255"
    }

    with modified_environment(**settings), device_launchers:

        runner = xmlrunner.XMLTestRunner(output='test-reports')

        test_classes = [getattr(test_module, s) for s in dir(test_module) if s.endswith("Tests")]

        if len(test_classes) < 1:
            raise ValueError("No test suites found in {}".format(test_module.__name__))

        for test_class in test_classes:
            print("Running tests in {}".format(test_class.__name__))
            test_suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner.run(test_suite)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Test an IOC under emulation by running tests against it')
    parser.add_argument('-l', '--list-devices',
                        help="List available devices for testing.", action="store_true")
    parser.add_argument('-pf', '--prefix', default=os.environ.get("MYPVPREFIX", None),
                        help='The instrument prefix; e.g. TE:NDW1373')
    parser.add_argument('-tm', '--test-module', default=None,
                        help="Test module to run")
    parser.add_argument('-e', '--emulator-path', default=None,
                        help="The path of the lewis.py file")
    parser.add_argument('-py', '--python-path', default="C:\Instrument\Apps\Python\python.exe",
                        help="The path of python.exe")
    parser.add_argument('-r', '--record-simulation', default=False, action="count",
                        help="Use record simulation rather than emulation (optional)")
    parser.add_argument('-ea', '--emulator-add-path', default=None,
                        help="Add path where device packages exist for the emulator.")
    parser.add_argument('-ek', '--emulator-device-package', default=None,
                        help="Name of packages where devices are found.")
    parser.add_argument('--var-dir', default=None,
                        help="Directory in which to create a log dir to write log file to and directory in which to "
                             "create tmp dir which contains environments variables for the IOC. Defaults to "
                             "environment variable ICPVARDIR and current dir if empty.")

    arguments = parser.parse_args()

    if arguments.list_devices:
        print("Available tests:")
        print('\n'.join(package_contents("tests")))
        sys.exit(0)

    var_dir = arguments.var_dir if arguments.var_dir is not None else os.getenv("ICPVARDIR", os.curdir)

    if arguments.prefix is None:
        print("Cannot run without instrument prefix")
        sys.exit(-1)

    elif arguments.test_module:

        if arguments.record_simulation:
            print("Running using record simulation")
        else:
            print("Running using device simulation")

        lewis = LewisNone("")
        test_module = load_module("tests.{}".format(arguments.test_module))

        try:
            iocs = test_module.IOCS
        except AttributeError:
            raise AttributeError("Expected module '{}' to contain an IOCS attribute".format(test_module.__name__))

        if len(iocs) < 1:
            raise ValueError("Need at least one IOC to launch")

        device_launchers = []
        for ioc in iocs:
            ioc_launcher = IocLauncher(device=ioc["name"], directory=ioc["directory"], macros=ioc["macros"],
                                       use_rec_sim=arguments.record_simulation, var_dir=var_dir)

            if "emulator" in ioc and not arguments.record_simulation:

                emulator_name = ioc["emulator"]
                emulator_protocol = ioc["emulator_protocol"] if "emulator_protocol" in ioc else "stream"
                emulator_device_package = ioc["emulator_package"] if "emulator_package" in ioc else "lewis_emulators"

                lewis_launcher = LewisLauncher(
                    device=emulator_name,
                    python_path=os.path.abspath(arguments.python_path),
                    lewis_path=os.path.abspath(arguments.emulator_path),
                    lewis_protocol=emulator_protocol,
                    lewis_additional_path=arguments.emulator_add_path,
                    lewis_package=emulator_device_package,
                    var_dir=var_dir
                )
            elif "emulator" in ioc:
                lewis_launcher = LewisNone(ioc["emulator"])
            else:
                lewis_launcher = None

            device_launchers.append(DeviceLauncher(ioc_launcher, lewis_launcher))

        run_test(arguments.prefix, test_module, DeviceCollectionLauncher(device_launchers))
    else:
        print("Type -h for help")
        sys.exit(-1)
