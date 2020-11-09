from ..monitor import Monitor
from ..collector import Collector
from ..spark_monitor import SparkMonitor
from ..merge import merge

__all__ = ["start_monitor", "start_collector", "start_spark_monitor", "merge_files"]

def start_monitor(addr="localhost", port=9822):
    m = Monitor(addr, int(port), verbose=True)
    m.start()


def start_collector(addr="0.0.0.0", port=9822):
    c = Collector(addr, int(port))
    c.start()


def start_spark_monitor(addr, port=9822):
    sm = SparkMonitor(addr, port)
    sm.start()


def merge_files(file1, file2):
    merge(file1, file2)