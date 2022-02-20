from kubemon.utils.data import filter_dict
from kubemon.utils.process import pid_exists
from kubemon.settings import Volatile
from kubemon.decorators import label
from ._docker import _load_metrics

from psutil import NoSuchProcess
from typing import List

import psutil

Volatile.set_procfs(psutil.__name__)

LABEL = 'mem'

@label(LABEL)
def _get_system_memory_usage(*args):
    fields = [
        'nr_active_file', 'nr_inactive_file', 'nr_mapped', 
        'nr_active_anon', 'nr_inactive_anon', 'pgpgin', 
        'pgpgout', 'pgfree', 'pgfault', 'pgmajfault', 'pgreuse'
    ]
        
    def to_dict(nested_lists):
        atoms = map(lambda atom_list: atom_list.split(), nested_lists)
        ret = {k: int(v) for k, v in atoms}
        return ret

    with open(f"{psutil.PROCFS_PATH}/vmstat", mode="r") as fd:
        data = fd.readlines()

    ret = to_dict(data)

    return filter_dict(ret, fields)

@label(LABEL)
def _get_process_memory_usage(pid: int) -> dict:
    """ 
    Returns the memory usage based on /proc virtual file system available in the Linux kernel. 
    Any questions, please refer to https://man7.org/linux/man-pages/man5/proc.5.html

    Args:
        pid (int)
    """

    if not pid_exists(pid):
        raise NoSuchProcess(pid)

    fields = [
        'size', 'resident', 'shared',
        'text', 'lib', 'data', 'dt'
    ]

    with open(f'{psutil.PROCFS_PATH}/{pid}/statm', mode='r') as fd:
        ret = fd.read()

    return {k: int(v) for k, v in zip(fields, ret.split())}

@label(LABEL)
def _get_docker_memory_usage(*paths: List[str]) -> dict:
    fields = [
        'rss', 'cache', 'mapped_file', 'pgpgin', 'pgpgout', 
        'pgfault', 'pgmajfault', 'active_anon', 'inactive_anon', 
        'active_file', 'inactive_file', 'unevictable'
    ]

    metrics = dict()
    for path in paths:
        metrics.update(_load_metrics(path))
    
    return filter_dict(metrics, fields)

METRIC_FUNCTIONS = {
    'os': _get_system_memory_usage,
    'process': _get_process_memory_usage,
    'docker': _get_docker_memory_usage,
}