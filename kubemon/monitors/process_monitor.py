from docker.models.containers import Container
from kubemon.monitors.base import BaseMonitor

from kubemon.settings import DISK_PARTITION, Volatile
from kubemon.utils.networking import get_host_ip, gethostname
from kubemon.log import create_logger
from kubemon.entities import (
    CPU, Memory,
    Network, Disk
)

import psutil

LOGGER = create_logger(__name__)

class ProcessMonitor(BaseMonitor):
    __slots__ = ( 
        '__pid', '__container', 
        '__name', '__metrics'
    )

    _type = 'process'

    def __init__(self, container: Container, pid: int):
        Volatile.set_procfs(psutil.__name__)
        try:
            psutil.Process(pid)
        except psutil.NoSuchProcess:
            LOGGER.info('pid %s not exist', pid)
            exit(0)

        self.__container = container
        self.__pid = pid
        self.__metrics = {
            'cpu': CPU(self._type),
            'memory': Memory(self._type),
            'disk': Disk(DISK_PARTITION, self._type),
            'network': Network(self._type),
        }

    @property
    def pid(self) -> int:
        return self.__pid

    @property
    def container(self) -> Container:
        return self.__container

    def __str__(self) -> str:
        ip = get_host_ip().replace('.', '_')
        return f'ProcessMonitor_{gethostname()}_{ip}_{self.__container.name}_{self.__pid}'
    
    def __repr__(self) -> str:
        return f'<ProcessMonitor - {gethostname()} - {get_host_ip()} - {self.__container.name} - {self.__pid}>'

    def get_disk_usage(self) -> dict:
        """ Returns the disk usage by a process """

        return self.__metrics['disk'](self.pid)

    def get_memory_usage(self) -> dict:
        """ Returns the memory usage by a process """

        return self.__metrics['memory'](self.pid)

    def get_cpu_usage(self) -> dict:
        """ Returns the cpu usage by a process """

        return self.__metrics['cpu'](self.pid)

    def get_net_usage(self) -> dict:
        """ Returns the network usage by a process """
        
        return self.__metrics['network'](self.pid)

    def get_stats(self) -> dict:
        cpu = self.get_cpu_usage()
        io = self.get_disk_usage()
        mem = self.get_memory_usage()
        net = self.get_net_usage()

        return {**cpu, **io, **mem, **net}

