from kubemon.monitors.base import BaseMonitor
from kubemon.settings import DISK_PARTITION, Volatile
from kubemon.entities import (
    CPU, Network,
    Memory, Disk
)
from kubemon.utils.data import subtract_dicts, filter_dict
from kubemon.utils.containers import get_container_pid
from kubemon.utils.networking import gethostname, get_host_ip

from kubemon.log import create_logger
from kubemon.pod import *

from time import sleep
from typing import Callable, List
from docker.models.containers import Container
from pathlib import Path

import psutil
import functools
import logging

__all__ = ['DockerMonitor']

LOGGER = create_logger(__name__)

class StatParser:
    ''' Class to parse docker metrics to fit into a CSV format, by saving into a flat dictionary. '''

    def _parse_blkio_operations(data: List[dict]) -> dict:
        ''' Auxiliary function to StatParser.blkio to remove 'Major' and 'Minor' keys. 
            This function gets only the operations made by blkio counter.
        '''
        ret = dict()
        for d in data:
            ret[d['op'].lower()] = d['value']
        return ret
    
    @staticmethod
    def blkio(data: dict) -> dict:
        ''' Retrieves the blkio counter statistics from a container '''
        ret = dict()
        for key, value in data.items():
            if value:
                value = StatParser._parse_blkio_operations(value)
                for k, v in value.items():
                    ret[f'{key}_{k}'] = v
        return ret

    @staticmethod
    def cpu(data: dict) -> dict:
        ''' Retrieves the cpu counter statistics from a container '''
        name_cpu = lambda x, suffix: {f'cpu{i}_{suffix}': val for i, val in enumerate(x)}
        ret = dict()

        for key, value in data.items():
            if isinstance(value, dict):
                ret[key] = dict()
                for k, v in data[key].items():
                    ret[key][f'cpu_{k}'] = v
            else:
                ret[key] = value

        ret = {
            **name_cpu(data['cpu_usage']['percpu_usage'], 'usage'),
            'system_cpu_usage': data['system_cpu_usage'],
            **data['throttling_data']
        }
        return ret

    @staticmethod
    def memory(data: dict) -> dict:
        ''' Retrieves the memory counter statistics from a container '''
        fields = ['rss', 'cache', 'mapped_file', 'pgpgin', 'pgpgout', 'pgfault', 'pgmajfault', 'active_anon', 'inactive_anon', 'active_file', 'inactive_file', 'unevictable']
        ret = dict()

        for k, v in data.items():
            ret[f'memory_{k}'] = v 
        
        ret = filter_dict(ret, fields)
        return ret
    
    @staticmethod
    def network(data: dict) -> dict:
        ''' Retrieves the network counter statistics from a container '''
        ret = dict()

        # Here it flattens the 'networks' dictionary(ies)
        for net in data:
            for k, v in data[net].items():
                ret[f'net_{net}_{k}'] = v

        return ret

def log(logger: logging.Logger):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            logger.info(f'Executed function {func.__name__}')
            return ret
        return wrapper
    return decorator

class DockerMonitor(BaseMonitor):
    __slots__ = ( 
        '__pid', '__container', 
        '__pod', '__pods', 
        '__name', '__stats_path',
        '_metrics', '_paths'
    )

    _type = 'docker'

    def __init__(self, container: Container, stats_path="/sys/fs/cgroup"):
        Volatile.set_procfs(psutil.__name__)
        
        self.__container = container
        self.__pid = get_container_pid(container)
        self.__stats_path = stats_path
        self._metrics = {
            'cpu': CPU(self._type),
            'network': Network(self._type),
            'disk': Disk(DISK_PARTITION, self._type),
            'memory': Memory(self._type)
        }

        self._paths = self._parse_cgroup(self.__pid, cgroup_path=stats_path)

    @property
    def stats_path(self):
        return self.__stats_path
    
    @property
    def pid(self) -> int:
        return self.__pid

    @property
    def container(self) -> Container:
        return self.__container

    def __str__(self) -> str:
        ip = get_host_ip().replace('.', '_')
        return f'DockerMonitor_{gethostname()}_{ip}_{self.__container.name}_{self.pid}'

    def __repr__(self) -> str:
        return f'<DockerMonitor - {gethostname()} - {get_host_ip()} - {self.__container.name} - {self.pid}>'

    @log(logger=LOGGER)
    def get_path(self, cgroup_controller: str, stat: str) -> str:
        """ 
        Get full path of the docker container within the pod, on cgroups directory 
        
        Args:
            cgroup_controller (str): cgroup controller. E.g. cpuacct, memory, blkio, etc.
            stat (str): file inside cgroup_controller
        """

        return self._paths[cgroup_controller] / stat

    def _parse_cgroup(self, container_pid: int, cgroup_path='/sys/fs/cgroup') -> dict:
        ignore = ['rdma', 'misc']

        path = f'{psutil.PROCFS_PATH}/{container_pid}/cgroup'

        with open(path, mode='r') as fp:
            data = fp.read()
        
        data = data.strip().split('\n')
        data = map(lambda x: x.split(':'), data)
        data = map(lambda x: x[1:], data)
        data = filter(lambda x: x[0] not in ignore, data)

        return {k: Path(cgroup_path + '/' + k + v) for k, v in data if k and not k.startswith('name')}

    @log(logger=LOGGER)
    def get_memory_usage(self) -> dict:
        """ Get the memory usage of a given container within a pod """
        path = self.get_path(cgroup_controller='memory', stat='memory.stat')

        return self._metrics['memory'](path)

    @log(logger=LOGGER)
    def get_disk_usage(self) -> dict:
        """ Get the disk usage of a given container within a pod """
        path = self.get_path(cgroup_controller='blkio', stat='blkio.throttle.io_service_bytes')
       
        return self._metrics['disk'](path)

    @log(logger=LOGGER)
    def get_cpu_times(self) -> dict:
        """ Get the CPU usage of a given container within a pod """
        path_cpuacct = self.get_path(cgroup_controller='cpu,cpuacct', stat='cpuacct.stat')
        path_cpu = self.get_path(cgroup_controller='cpu,cpuacct', stat='cpu.stat')

        return self._metrics['cpu'](path_cpuacct, path_cpu)

    @log(logger=LOGGER)
    def get_net_usage(self) -> dict:
        """ Get network usage of a given container within a pod 

        To understand why not gather information from cgroups, 
        please refer to https://docs.docker.com/config/containers/runmetrics/#network-metrics

        """

        return self._metrics['network'](self.pid)

    @log(logger=LOGGER)
    def get_stats(self) -> dict:
        """ Get all metrics of a given container within a pod """
        cpu = self.get_cpu_times()
        memory = self.get_memory_usage()
        network = self.get_net_usage()
        disk = self.get_disk_usage()

        return {**cpu, **memory, **network, **disk}
    