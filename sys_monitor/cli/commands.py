from ..monitor import Monitor
from ..collector import Collector
from ..spark_monitor import SparkMonitor


def start_monitor(addr="localhost", port=9822):
    m = Monitor(addr, int(port), verbose=True)
    m.start()


def start_collector(port=9822):
    c = Collector("0.0.0.0", int(port))
    c.start()


def start_spark_monitor(addr, port=9822):
    sm = SparkMonitor(addr, port)
    sm.start()
