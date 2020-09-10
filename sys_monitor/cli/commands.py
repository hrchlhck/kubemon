from ..monitor import Monitor
from ..collector import Collector


def start_monitor(addr, port):
    m = Monitor(addr, int(port), verbose=True)
    m.start()


def start_collector(addr, port):
    c = Collector(addr, int(port))
    c.start()