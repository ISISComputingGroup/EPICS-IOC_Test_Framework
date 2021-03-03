import sys
from caproto.threading.client import Context
from caproto._utils import CaprotoTimeoutError

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

    @exception_translator
    def set_pv_value(self, pv_name, value, wait=False, timeout=None):
        timeout = timeout or self._timeout
        pv = self._context.get_pvs(pv_name)[0]
        pv.write(value, wait=wait, timeout=timeout)

    @exception_translator
    def get_pv_value(self, pv_name):
        pv = self._context.get_pvs(pv_name)[0]
        result = pv.read()
        return result.data if result.data_count > 1 else result.data[0]


class UnableToConnectToPVException(Exception):
    pass


if __name__ == "__main__":
    ca = CaChannelWrapper()

    def cback(monitor, response):
        print(f"Got update from  {monitor.pv.name}: \n\n {response}")

    ca.add_monitor("wfm", cback)
    ca.add_monitor("value", cback)

    ca.set_pv_value("value", 9, timeout=1)
    ca.set_pv_value("wfm", [1, 2, 3, 4, 3, 43, 4, 5, 6])
    print(f"val: {ca.get_pv_value('value')}, wfm: {ca.get_pv_value('wfm')}")
