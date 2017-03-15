import os
import imp
import importlib
import unittest
import time
import argparse
from utils.lewis_launcher import LewisLauncher
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
    return importlib.import_module(name, )


def run_test(device, ioc_path, lewis_path, lewis_protocol):
    """
    Runs the tests for the specified IOC.

    :param device: the name of the IOC type
    :param ioc_path: the path to the folder containing the IOC's st.cmd
    :param lewis_path: the path to the Lewis start-up script
    :param lewis_protocol: the Lewis protocol to use
    """
    # Load the device's test module and get the class
    m = load_module('tests.%s' % device.lower())
    test_class = getattr(m, "%sTests" % device.capitalize())

    # Need to set epics address list to local broadcast otherwise channel access won't work
    os.environ['EPICS_CA_ADDR_LIST'] = "127.255.255.255"
    # Set IOC to dev sim mode
    os.environ['IFDEVSIM'] = ' '
    os.environ['IFNOTDEVSIM'] = '#'
    # Set port for IOC and Lewis to communicate over
    os.environ['EMULATOR_PORT'] = str(get_free_ports(1)[0])

    # Start Lewis
    if lewis_protocol is None:
        lewis = LewisLauncher(["python.exe",
                               lewis_path, "-e", "100",
                               device, "--", "--bind-address", "localhost", "--port", os.environ['EMULATOR_PORT']])
    else:
        lewis = LewisLauncher(["python.exe",
                               lewis_path, "-p", lewis_protocol,
                               "-e", "100",
                               device, "--", "--bind-address", "localhost", "--port", os.environ['EMULATOR_PORT']])

    # Start the IOC
    ioc = IocLauncher(ioc_path)
    # Need to give the IOC time to start
    print("Waiting for IOC to initialise")
    time.sleep(30)

    # Run the tests
    runner = unittest.TextTestRunner()
    test_suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    runner.run(test_suite)

    # Clean up
    lewis.close()
    ioc.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test an IOC under emulation by running tests against it')
    parser.add_argument('-l', '--list-devices', help='List available devices for testing.', action='store_true')
    parser.add_argument('-d', '--device', default=None, help='Device type to test.')
    parser.add_argument('-p', '--ioc-path', default=None, help="The path to the folder containing the IOC's st.cmd")
    parser.add_argument('-e', '--emulator-path', default=None, help="The path of the lewis.py file")
    parser.add_argument('-ep', '--emulator-protocol', default=None, help="The Lewis protocal to use (optional)")

    arguments = parser.parse_args()

    if arguments.list_devices:
        print "Available tests:"
        print '\n'.join(package_contents("tests"))
    elif arguments.device and arguments.ioc_path and arguments.emulator_path:
        run_test(arguments.device, os.path.abspath(arguments.ioc_path), os.path.abspath(arguments.emulator_path),
                 arguments.emulator_protocol)
    else:
        print "Type -h for help"
