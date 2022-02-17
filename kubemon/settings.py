from pathlib import Path

import logging

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
DATA_DIR = Path(f"/home/kubemon/kubemon-data")

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
