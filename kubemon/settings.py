from pathlib import Path

from dataclasses import dataclass

import logging
import sys

LOGGING_LEVEL = logging.INFO

## Monitors configuration
MONITOR_PORT = 9822
COLLECT_INTERVAL = 5
NUM_DAEMONS = 1

## CLI configuration
CLI_PORT = 9880
DAEMON_PORT = 9881
COLLECTOR_HEALTH_CHECK_PORT = 9882
COLLECTOR_INSTANCES_CHECK_PORT = 9883
COLLECT_TASK_PORT = 9884

## Disk configuration
DISK_PARTITION = 'sda'

# Directories
PROJECT_BASE = Path(__file__).absolute().parent.parent

## Logger path
LOG_PATH = PROJECT_BASE / 'logs'

## Data path
DATA_PATH = PROJECT_BASE / 'data'

# Starting message
START_MESSAGE = "OK"

# Creating base directory
if not PROJECT_BASE.exists():
    PROJECT_BASE.mkdir(parents=True)

# Creating log directory
if not LOG_PATH.exists():
    LOG_PATH.mkdir()

# Creating data directory
if not DATA_PATH.exists():
    DATA_PATH.mkdir()

@dataclass
class Volatile:
    PROCFS_PATH: str = '/procfs'
    NUM_DAEMONS: int = 1

    def set_procfs(module: str) -> None:
        sys.modules[module].PROCFS_PATH = Volatile.PROCFS_PATH
    
    def set_num_daemons(n: int) -> None:
        Volatile.NUM_DAEMONS = n