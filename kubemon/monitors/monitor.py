from kubemon.monitors.base import BaseMonitor
from kubemon.settings import DISK_PARTITION
from kubemon.entities import (
    CPU, Memory, 
    Network, Disk
)
from kubemon.utils.networking import get_host_ip, gethostname

class OSMonitor(BaseMonitor):
    _type = 'os'

    def get_stats(self):
        disk = Disk(DISK_PARTITION, self._type)
        cpu = CPU(self._type)
        net = Network(self._type)
        mem = Memory(self._type)

        return {**cpu(),**mem(),**disk(DISK_PARTITION),**net()}

    def __str__(self) -> str:
        ip = get_host_ip().replace('.', '_')
        return f'OSMonitor_{gethostname()}_{ip}'
    
    def __repr__(self) -> str:
        return f'<OSMonitor - {gethostname()} - {get_host_ip()}>'

