from docker.models.containers import Container

from ..utils import get_host_ip, get_default_nic
from .base_monitor import BaseMonitor
from ..log import create_logger

import psutil
import os
import socket
import re

def to_digit(x: str) -> object:
    return int(x) if x.isdigit() else x

def parse_proc_net(pid):
    # Assert if pid exists in /proc
    assert str(pid) in os.listdir('/proc')

    def to_dict(cols, vals):
        return {k: v for k, v in zip(cols, vals)}

    fd = f"/proc/{pid}/net/dev"
    with open(fd, mode='r') as fd:
        lines = list(fd)

        # Removing trailing whitespaces
        lines = list(map(lambda x: re.split(r'\W+', x), lines))
        
        for i, line in enumerate(lines):
            # Removing empty strings
            line = list(filter(None, line))

            # Converting to int
            lines[i] = list(map(to_digit, line))

        shift_factor = 9
        header = lines[1]
        
        # Labeling fields as tx or rx
        header[0] = 'iface'
        for i, field in enumerate(header[1:]):
            i = i + 1
            # shift_factor - 1 because its ignoring the 'face' field
            if i > shift_factor - 1:
                field = 'tx_' + field
            else:
                field = 'rx_' + field
            header[i] = field

        # Converting to dict
        for line in lines[2:]:
            yield to_dict(header, line)

LOGGER = create_logger(__name__)

class ProcessMonitor(BaseMonitor):
    __slots__ = ( 
        '__pid', '__container', 
        '__name',
    )

    def __init__(self, container: Container, pid: int):
        self.__container = container
        self.__pid = pid

    @property
    def pid(self) -> int:
        return self.__pid

    @property
    def container(self) -> Container:
        return self.__container

    def __str__(self) -> str:
        ip = get_host_ip().replace('.', '_')
        return f'ProcessMonitor_{socket.gethostname()}_{ip}_{self.__container.name}_{self.__pid}'
    
    def __repr__(self) -> str:
        return f'<ProcessMonitor - {socket.gethostname()} - {get_host_ip()} - {self.__container.name} - {self.__pid}>'

    @staticmethod
    def get_cpu_times(process: psutil.Process) -> dict:
        """ 
        Returns the CPU usage by a process. 

        Args:
            process (psutil.Process): The process that you want to get the data
        """
        ret = dict()
        cpu_data = process.cpu_times()
        ret['cpu_user'] = cpu_data.user
        ret['cpu_system'] = cpu_data.system
        ret['cpu_children_user'] = cpu_data.children_user
        ret['cpu_children_system'] = cpu_data.children_system
        ret['cpu_iowait'] = cpu_data.iowait

        return ret

    @staticmethod
    def get_io_counters(process: psutil.Process) -> dict:
        """ 
        Returns the disk usage by a process

        Args:
            process (psutil.Process): The process that you want to get the data
        """
        ret = dict()
        io_counters = process.io_counters()
        ret['io_read_count'] = io_counters.read_count
        ret['io_write_count'] = io_counters.write_count
        ret['io_read_bytes'] = io_counters.read_bytes
        ret['io_write_bytes'] = io_counters.write_bytes
        ret['io_read_chars'] = io_counters.read_chars
        ret['io_write_chars'] = io_counters.write_chars

        return ret

    @staticmethod
    def get_net_usage(pid: int) -> dict:
        """ 
        Returns the network usage by a process 

        Args:
            pid (int): The pid of the process
        """

        nic = [nic for nic in parse_proc_net(pid) if nic['iface'] == get_default_nic()]
        
        if len(nic) == 0:
            ret = {
                'iface': 'any', 'rx_bytes': 0, 'rx_packets': 0, 'rx_errs': 0, 
                'rx_drop': 0, 'rx_fifo': 0, 'rx_frame': 0, 'rx_compressed': 0, 
                'rx_multicast': 0, 'tx_bytes': 0, 'tx_packets': 0, 'tx_errs': 0, 
                'tx_drop': 0, 'tx_fifo': 0, 'tx_colls': 0, 'tx_carrier': 0, 
                'tx_compressed': 0
            }
        else:
            ret = nic[0]

        ret.pop('iface')
        return ret

    def get_stats(self) -> dict:
        try:
            process = psutil.Process(pid=self.pid)
            cpu = self.get_cpu_times(process)
            io = self.get_io_counters(process)
            mem = BaseMonitor.get_memory_usage(pid=self.pid)
            net = self.get_net_usage(process.pid)

            ret = {**cpu, **io, **mem, **net}
        except psutil.NoSuchProcess:
            ret = dict()

        return ret

