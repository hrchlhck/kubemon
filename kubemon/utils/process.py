from typing import List

from kubemon.settings import Volatile

import psutil

Volatile.set_procfs(psutil.__name__)

__all__ = ['pid_exists', 'get_children_pids']

def pid_exists(pid: int) -> bool:
    return pid in psutil.pids()

def get_children_pids(pid: int) -> List[int]:
    with open(f'{psutil.PROCFS_PATH}/{pid}/task/{pid}/children', 'r') as fp:
        pids = list(fp)
    
    if len(pids): pids = pids[0]
    else:
        pids = ''
    
    return list(map(int, pids.split()))