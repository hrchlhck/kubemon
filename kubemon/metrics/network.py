from typing import Dict
from psutil import NoSuchProcess

from kubemon.decorators import label
from kubemon.settings import Volatile
from kubemon.utils.networking import get_default_nic
from kubemon.utils.process import pid_exists

import psutil
import re

Volatile.set_procfs(psutil.__name__)

LABEL = 'net'

def _to_digit(x: str) -> object:
    return int(x) if x.isdigit() else x

def _to_dict(cols, vals):
    return {k: v for k, v in zip(cols, vals)}

def parse_proc_net(pid: int) -> Dict:

    if not pid_exists(pid):
        raise NoSuchProcess(pid)

    fd = f"{psutil.PROCFS_PATH}/{pid}/net/dev"
    with open(fd, mode='r') as fd:
        lines = list(fd)

        # Removing trailing whitespaces
        lines = list(map(lambda x: re.split(r'\W+', x), lines))
        
        for i, line in enumerate(lines):
            # Removing empty strings
            line = list(filter(None, line))

            # Converting to int
            lines[i] = list(map(_to_digit, line))

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
            yield _to_dict(header, line)

@label(LABEL)
def get_network_usage(pid: int) -> dict:
    """ Returns the network usage by a process 

        Args:
            pid (int): The pid of the process
    """

    if not pid_exists(pid):
        return NoSuchProcess(pid)

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

@label(LABEL)
def _get_os_net_usage(*args) -> dict:
    n = psutil.net_io_counters()
    nc = psutil.net_connections(kind='all')
    ret = {
        **n._asdict(),
        "num_connections": len(nc),
    }
    return ret

METRIC_FUNCTIONS = {
    'os': _get_os_net_usage,
    'process': get_network_usage,
    'docker': get_network_usage,
}