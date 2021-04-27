"""
Run the tests.
"""

import argparse
import os
import sys
import traceback
import unittest
from typing import List, Any

import six
import xmlrunner
import glob

from run_utils import package_contents, modified_environment
from run_utils import ModuleTests

from utils.device_launcher import device_launcher, device_collection_launcher
from utils.emulator_launcher import LewisLauncher, NullEmulatorLauncher, MultiLewisLauncher, Emulator, TestEmulatorData
from utils.ioc_launcher import IocLauncher, EPICS_TOP, IOCS_DIR
from utils.free_ports import get_free_ports
from utils.test_modes import TestModes


def clean_environment():
    """
    Cleans up the test environment between tests.
    """
    autosave_directory = os.path.join(var_dir, "autosave")
    files = glob.glob('{}/*SIM/*'.format(autosave_directory))
    for autosave_file in files:
        try:
            os.remove(autosave_file)
        except Exception as e:
            print("Failed to delete {}: {}".format(autosave_file, e))


def check_and_do_pre_ioc_launch_hook(ioc):
    """
    Check if the IOC dictionary contains a pre_ioc_launch_hook, if it does and is callable, call it, else do nothing.

    :param ioc: A dictionary representing an ioc.
    """
    do_nothing = lambda *args: None
    pre_ioc_launch_hook = ioc.get("pre_ioc_launch_hook", do_nothing)
    if callable(pre_ioc_launch_hook):
        pre_ioc_launch_hook()
    else:
        raise ValueError("Pre IOC launch hook not callable, so nothing has been done for it.")


def make_device_launchers_from_module(test_module, mode):
    """
    Returns a list of device launchers and directories for the given test module.
    Args:
        test_module: module containing IOC tests
        mode (TestModes): The mode to run in.

    Returns:
        list of device launchers (context managers which launch ioc + emulator pairs)
        set of device directories

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
    device_directories = set()
    for ioc in iocs:
        check_and_do_pre_ioc_launch_hook(ioc)
        free_port = get_free_ports(2)
        device_directories.add(ioc["directory"])
        try:
            macros = ioc["macros"]
        except KeyError:
            macros = {}
            ioc["macros"] = macros
        emmulator_port = free_port[0]
        macros['EMULATOR_PORT'] = emmulator_port
        macros['LOG_PORT'] = free_port[1]

        ioc_launcher_class = ioc.get("ioc_launcher_class", IocLauncher)
        ioc_launcher = ioc_launcher_class(test_module.__name__, ioc, mode, var_dir)

        if "emulator" in ioc and mode != TestModes.RECSIM:
            emulator_launcher_class = ioc.get("emulator_launcher_class", LewisLauncher)
            emulator_launcher = emulator_launcher_class(test_module.__name__, ioc["emulator"], var_dir,
                                                        emmulator_port, ioc)
        elif "emulator" in ioc:
            emulator_launcher = NullEmulatorLauncher(test_module.__name__, ioc["emulator"], var_dir, None, ioc)
        elif "emulators" in ioc and mode != TestModes.RECSIM:
            emulator_launcher_class = ioc.get("emulators_launcher_class", MultiLewisLauncher)
            test_emulator_data: List[TestEmulatorData] = ioc.get("emulators", [])
            emulator_list: List[Emulator] = []
            for test_emulator in test_emulator_data:
                emulator_list.append(
                    Emulator(
                        test_emulator.launcher_address, test_emulator.emulator,
                        os.path.join(var_dir, f"{test_emulator.emulator}_{test_emulator.launcher_address}"),
                        test_emulator.emulator_port, ioc
                    )
                )
            emulator_launcher = emulator_launcher_class(test_module.__name__, emulator_list)
        else:
            emulator_launcher = None

        device_launchers.append(device_launcher(ioc_launcher, emulator_launcher))

    return device_launchers, device_directories


def load_and_run_tests(test_names, failfast, report_coverage, ask_before_running_tests, tests_mode=None):
    """
    Loads and runs the dotted unit tests to be run.

    Args:
        test_names: List of dotted unit tests to run.
        failfast: Determines if tests abort after first failure.
        report_coverage: Report test coverage of test modules versus ioc directories.
        ask_before_running_tests: ask whether to run the tests before running them
        tests_mode: test mode to run (default: both RECSIM and DEVSIM)

    Returns:
        boolean: True if all tests pass and false otherwise.
    """

    modules_to_be_loaded = sorted({test.split(".")[0].strip() for test in test_names})
    modules_to_be_tested = [ModuleTests(module) for module in modules_to_be_loaded]

    modes = set()
    tested_ioc_directories = set()

    for module in modules_to_be_tested:
        # Add tests that are either the module or a subset of the module i.e. module.TestClass
        module.tests = [test for test in test_names if test == module.name or test.startswith(module.name + ".")]
        modes.update(module.modes)

    test_results = []

    for mode in modes:
        if tests_mode is not None and mode != tests_mode:
            continue

        modules_to_be_tested_in_current_mode = [module for module in modules_to_be_tested if mode in module.modes]

        for module in modules_to_be_tested_in_current_mode:
            clean_environment()
            device_launchers, device_directories = make_device_launchers_from_module(module.file, mode)
            tested_ioc_directories.update(device_directories)
            test_results.append(
                run_tests(arguments.prefix, module.name, module.tests, device_collection_launcher(device_launchers),
                          failfast, ask_before_running_tests))

    if report_coverage:
        report_test_coverage_for_devices(tested_ioc_directories)

    return all(test_result is True for test_result in test_results)


def prompt_user_to_run_tests(test_names):
    """
    Utility function to ask the user whether to begin the tests

    Args:
        test_names: List of IOC test names to be run

    Returns:
        None

    """
    print("Run tests? [Y/N]: {}".format(test_names))
    while True:
        answer = six.moves.input()
        if answer == "" or answer.upper()[0] not in ["N", "Y"]:
            print("Answer must be Y or N")
        elif answer.upper()[0] == "N":
            print("Not running tests, emulator and IOC only. Ctrl+c to quit.")
        elif answer.upper()[0] == "Y":
            return


def report_test_coverage_for_devices(tested_directories):
    """
    Report the ioc directories not tested

    Args:
        tested_directories (list): List of IOC boot directories generated by make_device_launchers_from_module

    Returns:
        None
    """
    # get names of iocs from ioc folder
    iocs = []
    for dir in os.listdir(IOCS_DIR):
        if os.path.isdir(os.path.join(IOCS_DIR, dir)):
            iocs.append(dir)
    iocs = set(ioc.lower() for ioc in iocs)

    tested_iocs = []
    for dir in tested_directories:
        # Get the 3rd folder up from the ioc boot directory (should be device name) in lowercase
        tested_iocs.append(os.path.normpath(dir).split(os.path.sep)[-3].lower())

    tested_iocs = set(tested_iocs)
    missing_tests = sorted(iocs.difference(tested_iocs))

    print("\nThe following IOCs have not been tested:\n")
    for test in missing_tests:
        print(test)


class ReportFailLoadTestsuiteTestCase(unittest.TestCase):
    """
    Class to allow reporting of an error to run any tests.

    Args:
        failing_module_name:   Name of module that failed.
        msg:                   Error message explaining failure.

    Returns:
        None
    """

    def __init__(self, failing_module_name, msg):
        # strictly we should use and pass (*args, **kwargs) but we only call 
        # this directly ourselves and not from a test suite.
        # We create a function based on fail_with_msg() to get a better test summary.
        func_name = "{}_module_failed_to_load".format(failing_module_name)
        setattr(self, func_name, self.fail_with_msg)
        super(ReportFailLoadTestsuiteTestCase, self).__init__(func_name)
        self.msg = msg

    def fail_with_msg(self):
        """
        Function to be used as basis of "runTest" unittest.TestCase function.
        """
        self.fail(self.msg)


def run_tests(prefix, module_name, tests_to_run, device_launchers, failfast_switch, ask_before_running_tests=False):
    """
    Runs dotted unit tests.

    Args:
        prefix: The instrument prefix.
        module_name: Name of module containing tests.
        tests_to_run: List of dotted unit tests to be run.
        device_launchers: Context manager that launches the necessary iocs and associated emulators.
        failfast_switch: Determines if test suit aborts after first failure.
        ask_before_running_tests: ask whether to run the tests before running them

    Returns:
        bool: True if all tests pass and false otherwise.
    """
    os.environ["testing_prefix"] = prefix

    # Need to set epics address list to local broadcast otherwise channel access won't work
    settings = {
        'EPICS_CA_ADDR_LIST': "127.255.255.255"
    }

    test_names = ["{}.{}".format(arguments.tests_path, test) for test in tests_to_run]

    runner = xmlrunner.XMLTestRunner(output='test-reports', stream=sys.stdout, failfast=failfast_switch)
    test_suite = unittest.TestLoader().loadTestsFromNames(test_names)

    try:
        with modified_environment(**settings), device_launchers:
            if ask_before_running_tests:
                prompt_user_to_run_tests(test_names)
            result = runner.run(test_suite).wasSuccessful()
    except Exception:
        msg = "Error while attempting to load test suite: {}".format(traceback.format_exc())
        result = runner.run(ReportFailLoadTestsuiteTestCase(module_name, msg)).wasSuccessful()
    return result


if __name__ == '__main__':
    if six.PY2:
        print("IOC system tests should now be run under python 3. Aborting.")
        sys.exit(-1)

    pythondir = os.environ.get("PYTHONDIR", None)

    if pythondir is not None:
        emulator_path = os.path.join(pythondir, "scripts")
    else:
        emulator_path = None

    parser = argparse.ArgumentParser(
        description='Test an IOC under emulation by running tests against it')
    parser.add_argument('-l', '--list-devices',
                        help="List available devices for testing.", action="store_true")
    parser.add_argument('-rc', '--report-coverage',
                        help='Report devices that have not been tested.', action="store_true")
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
    parser.add_argument('-tp', '--tests-path', default="tests",
                        help="""Path to find the tests in, this must be a valid python module. 
                        Default is in the tests folder of this repo""")
    parser.add_argument('-f', '--failfast', action='store_true',
                        help="""Determines if the rest of tests are skipped after the first failure""")
    parser.add_argument('-a', '--ask-before-running', action='store_true',
                        help="""Pauses after starting emulator and ioc. Allows you to use booted
                        emulator/IOC or attach debugger for tests""")
    parser.add_argument('-tm', '--tests-mode', default=None, choices=['DEVSIM', 'RECSIM'],
                        help="""Tests mode to run e.g. DEVSIM or RECSIM (default: both).""")

    arguments = parser.parse_args()

    if os.path.dirname(arguments.tests_path):
        full_path = os.path.abspath(arguments.tests_path)
        if not os.path.isdir(full_path):
            print("Test path {} not found".format(full_path))
            sys.exit(-1)
        tests_module_path = os.path.dirname(full_path)
        sys.path.insert(0, tests_module_path)
        arguments.tests_path = os.path.basename(arguments.tests_path)

    if arguments.list_devices:
        print("Available tests:")
        print('\n'.join(sorted(package_contents(arguments.tests_path))))
        sys.exit(0)

    var_dir = arguments.var_dir if arguments.var_dir is not None else os.getenv("ICPVARDIR", os.curdir)
    var_dir = var_dir.replace('/', '\\')

    if arguments.prefix is None:
        print("Cannot run without instrument prefix, you may need to run this using an EPICS terminal")
        sys.exit(-1)

    if arguments.emulator_path is None:
        print("Cannot run without emulator path, you may need to run this using an EPICS terminal")
        sys.exit(-1)

    tests = arguments.tests if arguments.tests is not None else package_contents(arguments.tests_path)
    failfast = arguments.failfast
    report_coverage = arguments.report_coverage
    ask_before_running_tests = arguments.ask_before_running

    tests_mode = None
    if arguments.tests_mode == "RECSIM":
        tests_mode = TestModes.RECSIM
    if arguments.tests_mode == "DEVSIM":
        tests_mode = TestModes.DEVSIM

    try:
        success = load_and_run_tests(tests, failfast, report_coverage, ask_before_running_tests, tests_mode)
    except Exception as e:
        print("---\n---\n---\nAn Error occurred loading the tests: ")
        traceback.print_exc()
        print("---\n---\n---\n")
        success = False

    sys.exit(0 if success else 1)
