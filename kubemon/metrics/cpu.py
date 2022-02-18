from kubemon.settings import Volatile
from kubemon.decorators import label
from ._docker import _load_metrics

import psutil

Volatile.set_procfs(psutil.__name__)

LABEL = 'cpu'

@label(LABEL)
def _os_cpu_usage(*args):
    metrics = {
        **psutil.cpu_stats()._asdict(),
        **psutil.cpu_times()._asdict(),
    }

    return metrics

@label(LABEL)
def _process_cpu_usage(pid: int):
    p = psutil.Process(pid)
    return p.cpu_times()._asdict()

@label(LABEL)
def _container_cpu_usage(*paths):
    metrics = dict()
    for path in paths:
        metrics.update(_load_metrics(path))
    return metrics


METRIC_FUNCTIONS = {
    'os': _os_cpu_usage,
    'process': _process_cpu_usage,
    'docker': _container_cpu_usage,
}