from kubemon.settings import DISK_PARTITION
from kubemon.entities import (
    CPU, Memory, 
    Network, Disk
)
from kubemon.utils import get_host_ip, gethostname

class OSMonitor:
    def get_stats(self):
        _type = 'os'
        disk = Disk(DISK_PARTITION, _type)
        cpu = CPU(_type)
        net = Network(_type)
        mem = Memory(_type)

        return {**cpu(),**mem(),**disk(DISK_PARTITION),**net()}

    def __str__(self) -> str:
        ip = get_host_ip().replace('.', '_')
        return f'OSMonitor_{gethostname()}_{ip}'
    
    def __repr__(self) -> str:
        return f'<OSMonitor - {gethostname()} - {get_host_ip()}>'

