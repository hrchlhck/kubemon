from pathlib import Path
import logging

LOGGING_LEVEL = logging.DEBUG

# Directories
DATA_DIR = Path(f"/home/kubemon/kubemon-data")

## Logger path
LOG_PATH = DATA_DIR / 'logs'

## Data path
DATA_PATH = DATA_DIR / 'data'

# Starting message
START_MESSAGE = "OK"

# Monitors configuration
DEFAULT_MONITOR_PORT = 9822
DEFAULT_MONITOR_INTERVAL = 5
MONITOR_PROBE_INTERVAL = 5

# CLI configuration
DEFAULT_CLI_PORT = 9880
DEFAULT_DAEMON_PORT = 9881

# Disk configuration
DEFAULT_DISK_PARTITION = 'sda'

# Creating base directory
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)

# Creating log directory
if not LOG_PATH.exists():
    LOG_PATH.mkdir()

# Creating data directory
if not DATA_PATH.exists():
    DATA_PATH.mkdir()
