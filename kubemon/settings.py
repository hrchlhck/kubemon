from pathlib import Path

from dataclasses import dataclass

import logging
import sys
import os

def _check_environ(var: str) -> bool:
    return var in os.environ

VARS = (
    'MONITOR_PORT',
    'NUM_DAEMONS',
    'SERVICE_NAME',
    'COLLECT_INTERVAL',
    'OUTPUT_DIR',
    'NAMESPACES',
    'FROM_K8S',
)

LOGGING_LEVEL = logging.INFO
PROJECT_BASE = Path(__file__).absolute().parent.parent

if 'WITHIN_DOCKER' in os.environ:
    for var in VARS:
        if not _check_environ(var):
            raise EnvironmentError(f'Missing {var} env. var.')

    ## Monitors configuration
    MONITOR_PORT = int(os.environ['MONITOR_PORT'])
    COLLECT_INTERVAL = int(os.environ['COLLECT_INTERVAL'])
    NUM_DAEMONS = int(os.environ['NUM_DAEMONS'])
    SERVICE_NAME = os.environ['SERVICE_NAME']
    K8S_NAMESPACES = os.environ['NAMESPACES'].split()
    FROM_K8S = True if os.environ['FROM_K8S'].lower() == 'true' else False
    DATA_DIR = PROJECT_BASE / os.environ['OUTPUT_DIR']
else:
    MONITOR_PORT = 80
    COLLECT_INTERVAL = 5
    NUM_DAEMONS = 1
    SERVICE_NAME = 'monitor'
    K8S_NAMESPACES = ''
    FROM_K8S = False
    DATA_DIR = PROJECT_BASE / 'output'

## CLI configuration
CLI_PORT = 9880
COLLECTOR_HEALTH_CHECK_PORT = 9882

## Disk configuration
DISK_PARTITION = 'sda'

# Directories

## Logger path
LOG_PATH = DATA_DIR / 'logs'

## Data path
DATA_PATH = DATA_DIR / 'data'

# Starting message
START_MESSAGE = "OK"

# Creating base directory
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)

# Creating log directory
if not LOG_PATH.exists():
    LOG_PATH.mkdir()

# Creating data directory
if not DATA_PATH.exists():
    DATA_PATH.mkdir()

nd = NUM_DAEMONS

@dataclass
class Volatile:
    PROCFS_PATH: str = '/procfs'
    NUM_DAEMONS: int = nd

    def set_procfs(module: str) -> None:
        sys.modules[module].PROCFS_PATH = Volatile.PROCFS_PATH
    
    def set_num_daemons(n: int) -> None:
        Volatile.NUM_DAEMONS = n
