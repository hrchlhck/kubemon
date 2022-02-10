from kubemon.config import DISK_PARTITION
from .base_monitor import BaseMonitor
from ..entities.cpu import CPU
from ..entities.disk import Disk
from ..entities.network import Network
from ..utils import get_host_ip

import socket

class OSMonitor(BaseMonitor):   
    def get_stats(self):
        disk = Disk(disk_name=DISK_PARTITION).get_usage()
        cpu = CPU().get_usage
        net = Network().get_usage
        mem = BaseMonitor.get_memory_usage()
        data = {
            **cpu,
            **mem,
            **disk.infos,
            **net,
        }

        return data

    def __str__(self) -> str:
        ip = get_host_ip().replace('.', '_')
        return f'OSMonitor_{socket.gethostname()}_{ip}'
    
    def __repr__(self) -> str:
        return f'<OSMonitor - {socket.gethostname()} - {get_host_ip()}>'

