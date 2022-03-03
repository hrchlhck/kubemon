from psutil import NoSuchProcess
from typing import Generator

from ._docker import _load_metrics
from kubemon.decorators import label
from kubemon.settings import Volatile
from kubemon.utils.process import pid_exists

import psutil

Volatile.set_procfs(psutil.__name__)

LABEL = 'disk'

class Partition:
    """ Class for a simple representation of a disk partition on a Linux based system.
        For more information about the attributes, please refer to https://www.kernel.org/doc/html/latest/block/stat.html
    """

    def __init__(self, partition_name, *fields, flush_io=0, flush_ticks=0):
        self.__partition_name = partition_name
        _fields = [
            'read_io', 'read_merge', 'read_sectors',
            'read_ticks', 'write_io', 'write_merge',
            'write_sectors', 'write_ticks', 'in_flight',
            'io_ticks', 'time_in_queue', 'discard_io',
            'discard_merges', 'discard_sectors','discard_ticks',
        ]

        self.__info = {k: v for k, v in zip(_fields, fields[:len(_fields)])}

        if flush_io and flush_ticks:
            self.__info.update({"flush_io": flush_io, "flush_ticks": flush_ticks})

    @property
    def name(self):
        return self.__partition_name

    def __getitem__(self, info):
        return self.__info[info]
    
    def items(self):
        return self.__info.items()

    def __str__(self):
        base = f'<Partition partition={self.name}, '
        metrics = ', '.join(f'{k}={v}' for k, v in self.__info.items())
        base += metrics
        base += '>'
        return base

    def __repr__(self):
        return self.__str__()

def _usage_generator(*partitions, all_partitions=False, partition='sda') -> Generator:
    """ Returns a generator for each partition """
    if not all_partitions:
        yield _parse_data(partition)
    else:
        for _partition in partitions:
            yield _parse_data(_partition)

def _parse_data(partition_name: str) -> Partition:
    """ Parses /sys/block/<partition_name>/stat file and returns a 'Partition' object"""
    filename = "/sys/block/{}/stat".format(partition_name)
    with open(filename, "r") as f:
        data = f.read()
    data = list(map(int, data.split()))
    return Partition(partition_name, *data)

@label(LABEL)
def _get_process_disk_usage(pid: int) -> dict:
    if not pid_exists(pid):
        raise NoSuchProcess(pid)
    
    p = psutil.Process(pid)

    return p.io_counters()._asdict()

@label(LABEL)
def _get_os_disk_usage(partition: str, all_partitions=False) -> dict:
    """ Get information from a partition or from all available partitions started with 'sd' """
    ret = tuple(_usage_generator(all_partitions, partition))

    if not all_partitions:
        return ret[0]
    return ret

def _rename_fields(fields: tuple) -> str:
    partition = fields[0]
    field = fields[1]
    value = fields[2]
    return f'{partition}_{field.lower()}', value
    
@label(LABEL)
def _get_container_disk_usage(*paths: str) -> dict:
    metrics = dict()
    for path in paths:
        data = _load_metrics(path)
        data = filter(lambda x: len(x) == 3, data)
        data = map(_rename_fields, data)
        data = {k: v for k, v in data}
        metrics.update(data)
    return metrics

METRIC_FUNCTIONS = {
    'os': _get_os_disk_usage,
    'process': _get_process_disk_usage,
    'docker': _get_container_disk_usage,
}