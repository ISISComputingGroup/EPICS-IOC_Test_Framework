"""
Run the tests.
"""

import argparse
import os
import sys
import traceback
import unittest
import xmlrunner

from run_utils import package_contents, modified_environment
from run_utils import ModuleTests

from utils.device_launcher import device_launcher, device_collection_launcher
from utils.lewis_launcher import LewisLauncher, LewisNone
from utils.ioc_launcher import IocLauncher, EPICS_TOP
from utils.free_ports import get_free_ports
from utils.test_modes import TestModes


def make_device_launchers_from_module(test_module, mode):
    """
    Returns a list of device launchers for the given test module.
    Args:
        test_module: module containing IOC tests
        mode (TestModes): The mode to run in.

    Returns:
        list of device launchers (context managers which launch ioc + emulator pairs)

    """
    try:
        iocs = test_module.IOCS
    except AttributeError:
        raise AttributeError("Expected module '{}' to contain an IOCS attribute".format(test_module.__name__))

    if len(iocs) < 1:
        raise ValueError("Need at least one IOC to launch")

    for ioc in iocs:
        if "name" not in ioc:
            raise ValueError("IOC entry must have a 'name' attribute which should give the IOC name")
        if "directory" not in ioc:
            raise ValueError("IOC entry must have a 'directory' attribute which should give the path to the IOC")

    print("Testing module {} in {} mode.".format(test_module.__name__, TestModes.name(mode)))

    device_launchers = []
    for ioc in iocs:

        free_port = get_free_ports(2)
        try:
            macros = ioc["macros"]
        except KeyError:
            macros = {}
            ioc["macros"] = macros
        emmulator_port = free_port[0]
        macros['EMULATOR_PORT'] = emmulator_port
        macros['LOG_PORT'] = free_port[1]

        launcher = ioc.get("LAUNCHER", IocLauncher)

        ioc_launcher = launcher(ioc, mode, var_dir)

        if "emulator" in ioc and mode != TestModes.RECSIM:

            emulator_device = ioc["emulator"]
            emulator_id = ioc.get("emulator_id", emulator_device)
            emulator_protocol = ioc.get("emulator_protocol", "stream")
            emulator_device_package = ioc.get("emulator_package", "lewis_emulators")
            emulator_full_path = ioc.get("emulator_path",
                                         os.path.join(EPICS_TOP, "support", "DeviceEmulator", "master"))

            lewis_launcher = LewisLauncher(
                device=emulator_device,
                python_path=os.path.abspath(arguments.python_path),
                lewis_path=os.path.abspath(arguments.emulator_path),
                lewis_protocol=emulator_protocol,
                lewis_additional_path=emulator_full_path,
                lewis_package=emulator_device_package,
                var_dir=var_dir,
                port=emmulator_port,
                emulator_id=emulator_id
            )

        elif "emulator" in ioc:
            emulator_id = ioc.get("emulator_id", ioc["emulator"])
            lewis_launcher = LewisNone(emulator_id)
        else:
            lewis_launcher = None

        device_launchers.append(device_launcher(ioc_launcher, lewis_launcher))

    return device_launchers


def load_and_run_tests(test_names, failfast):
    """
    Loads and runs the dotted unit tests to be run.

    Args:
        test_names: List of dotted unit tests to run.
        failfast: Determines if tests abort after first failure.

    Returns:
        boolean: True if all tests pass and false otherwise.
    """

    modules_to_be_loaded = sorted({test.split(".")[0].strip() for test in test_names})
    modules_to_be_tested = [ModuleTests(module) for module in modules_to_be_loaded]

    modes = set()

    for module in modules_to_be_tested:
        module.tests = [test for test in test_names if test.startswith(module.name)]
        modes.update(module.modes)

    test_results = []

    for mode in modes:
        modules_to_be_tested_in_current_mode = [module for module in modules_to_be_tested if mode in module.modes]

        for module in modules_to_be_tested_in_current_mode:
            device_launchers = make_device_launchers_from_module(module.file, mode)
            test_results.append(
                run_tests(arguments.prefix, module.tests, device_collection_launcher(device_launchers), failfast))

    return all(test_result is True for test_result in test_results)


def run_tests(prefix, tests_to_run, device_launchers, failfast_switch):
    """
    Runs dotted unit tests.

    Args:
        prefix: The instrument prefix.
        tests_to_run: List of dotted unit tests to be run.
        device_launchers: Context manager that launches the necessary iocs and associated emulators.
        failfast_switch: Determines if test suit aborts after first failure.

    Returns:
        bool: True if all tests pass and false otherwise.
    """
    os.environ["testing_prefix"] = prefix

    # Need to set epics address list to local broadcast otherwise channel access won't work
    settings = {
        'EPICS_CA_ADDR_LIST': "127.255.255.255"
    }

    test_names = ["tests.{}".format(test) for test in tests_to_run]

    with modified_environment(**settings), device_launchers:

        runner = xmlrunner.XMLTestRunner(output='test-reports', stream=sys.stdout, failfast=failfast_switch)

        test_suite = unittest.TestLoader().loadTestsFromNames(test_names)
        result = runner.run(test_suite).wasSuccessful()

    return result


if __name__ == '__main__':

    pythondir = os.environ.get("PYTHONDIR", None)

    if pythondir is not None:
        emulator_path = os.path.join(pythondir, "scripts")
    else:
        emulator_path = None

    parser = argparse.ArgumentParser(
        description='Test an IOC under emulation by running tests against it')
    parser.add_argument('-l', '--list-devices',
                        help="List available devices for testing.", action="store_true")
    parser.add_argument('-pf', '--prefix', default=os.environ.get("MYPVPREFIX", None),
                        help='The instrument prefix; e.g. TE:NDW1373')
    parser.add_argument('-e', '--emulator-path', default=emulator_path,
                        help="The path of the lewis.py file")
    parser.add_argument('-py', '--python-path', default="C:\Instrument\Apps\Python\python.exe",
                        help="The path of python.exe")
    parser.add_argument('--var-dir', default=None,
                        help="Directory in which to create a log dir to write log file to and directory in which to "
                             "create tmp dir which contains environments variables for the IOC. Defaults to "
                             "environment variable ICPVARDIR and current dir if empty.")
    parser.add_argument('-t', '--tests', default=None, nargs="+",
                        help="""Dotted names of tests to run. These are of the form module.class.method.
                        Module just runs the tests in a module. 
                        Module.class runs the the test class in Module.
                        Module.class.method runs a specific test.""")
    parser.add_argument('-f', '--failfast', action='store_true',
                        help="""Determines if the rest of tests are skipped after the first failure""")

    arguments = parser.parse_args()

    if arguments.list_devices:
        print("Available tests:")
        print('\n'.join(package_contents("tests")))
        sys.exit(0)

    var_dir = arguments.var_dir if arguments.var_dir is not None else os.getenv("ICPVARDIR", os.curdir)
    var_dir = var_dir.replace('/', '\\')

    if arguments.prefix is None:
        print("Cannot run without instrument prefix")
        sys.exit(-1)

    if arguments.emulator_path is None:
        print("Cannot run without emulator path")
        sys.exit(-1)

    tests = arguments.tests if arguments.tests is not None else package_contents("tests")
    failfast = arguments.failfast

    try:
        success = load_and_run_tests(tests, failfast)
    except Exception as e:
        print("---\n---\n---\nAn Error occurred loading the tests: ")
        traceback.print_exc()
        print("---\n---\n---\n")
        success = False

    sys.exit(0 if success else 1)
