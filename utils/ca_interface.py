import sys
from caproto.threading.client import Context
from caproto._utils import CaprotoTimeoutError
from caproto import ChannelType

def exception_translator(func):
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CaprotoTimeoutError:
            raise UnableToConnectToPVException(sys.exc_info()[1])
    return inner_function


class CaChannelWrapper:
    def __init__(self, default_ca_timeout=5):
        self._context = Context(timeout=default_ca_timeout)
        self._timeout = self._context.timeout

    def add_monitor(self, pv_name, callback=None):
        """
        callback function must have call signature:

            def f(monitor, response):
              ...

        The name of pv that fired the monitor event is available as
        monitor.pv.name

        see https://nsls-ii.github.io/caproto/threading-client.html
        """

        pv = self._context.get_pvs(pv_name)[0]
        monitor = pv.subscribe()
        if callback:
            monitor.add_callback(callback)

    def poll(self):
        pass

    def errorLogFunc(self, *args, **kwargs):
        return None
    
    def pv_exists(self, pv_name, timeout=None):
        timeout = timeout or self._timeout
        pv = self._context.get_pvs(pv_name)[0]
        try:
            pv.read()
            return True
        except CaprotoTimeoutError:
            return False

    @exception_translator
    def set_pv_value(self, pv_name, value, wait=False, timeout=None):
        timeout = timeout or self._timeout
        pv = self._context.get_pvs(pv_name)[0]
        pv.write(value, wait=wait, timeout=timeout)

    @exception_translator
    def get_pv_value(self, pv_name):
        pv = self._context.get_pvs(pv_name)[0]
        result = pv.read()
        received_data = result.data
        #Deal with string/bytes in P3
        if result.data_type == ChannelType.STRING:
            received_data = self.decode_bytes_if_necessary(received_data)
        return received_data if len(received_data) > 1 else received_data[0]

    @staticmethod
    def decode_bytes_if_necessary(data_list):
        if not type(data_list[0]) == bytes:
            return data_list
        return [element.decode() for element in data_list]



class UnableToConnectToPVException(Exception):
    pass

