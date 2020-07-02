class UnableToConnectToEmulatorException(IOError):
    """
    The system is unable to connect to the emulator for some pv_name.
    """
    def __init__(self, emulator_name, err):
        super(UnableToConnectToEmulatorException, self).__init__("Unable to connect to Emnulator {0}: {1}"
                                                                 .format(emulator_name, err))
