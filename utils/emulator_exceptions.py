class UnableToConnectToEmulatorException(IOError):  # noqa: N818 (historic name)
    """
    The system is unable to connect to the emulator for some reason.
    """

    def __init__(self, emulator_name: str, err: str | BaseException) -> None:
        super(UnableToConnectToEmulatorException, self).__init__(
            "Unable to connect to Emnulator {0}: {1}".format(emulator_name, err)
        )
