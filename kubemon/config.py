from pathlib import Path
import sys

# Directories
BASE_DIR = Path(__file__).parent.parent
if 'win' in sys.platform:
    ROOT_DIR = BASE_DIR
else:
    ROOT_DIR = "/tmp/data"

# Starting message
START_MESSAGE = "OK"

# Monitors configuration
DEFAULT_MONITOR_PORT = 9822
DEFAULT_MONITOR_INTERVAL = 5

# CLI configuration
DEFAULT_CLI_PORT = 9880

# Disk configuration
DEFAULT_DISK_PARTITION = 'sda'