from pathlib import Path

import logging

LOGGING_LEVEL = logging.INFO

PROJECT_DIR = Path(__file__).absolute().parent.parent

class Configuration:
    def __init__(self, conf: dict):
        self.__conf = conf
    
    def __getitem__(self, val: str) -> str:
        if val not in self.__conf:
            raise KeyError(f'The configuration file is missing \'{val}\' key.')
        return self.__conf[val]
    
    def __str__(self) -> str:
        return str(self.__conf)
    
    def __repr__(self) -> str:
        return repr(self.__conf)

class ConfigParser:   
    @staticmethod
    def _map_values(x, delimiter):
        if delimiter and delimiter in x:
            if x.count(delimiter) > 1:
                ret = x.split(delimiter * x.count(delimiter))
            else:
                ret = x.split(delimiter)
            if len(ret) == 2:
                val = int(ret[1]) if ret[1][0].isdigit() else ret[1]
                return {ret[0]: val}
        else:
            return x

    @staticmethod
    def _clear(x, chars="\n\r"):
        for c in chars:
            x = x.replace(c, "")
        return x

    @classmethod
    def parse(cls, path, delimiter="@"):
        with open(path, mode='r') as fd:
            data = list(fd)
        
        # Remove comments
        data = filter(lambda x: not x.startswith('#') and not x.startswith('\n'), data)
        
        # Remove junk characters
        data = map(lambda x: cls._clear(x), data)

        # Parse key:value
        data = map(lambda x: cls._map_values(x, delimiter=delimiter), data)

        ret = dict()

        for d in data:
            ret.update(d)

        return Configuration(ret)

CONFIGURATION = ConfigParser.parse((PROJECT_DIR / 'kubemon.conf'), delimiter=' ')

CLI_PORT = CONFIGURATION['CLI_PORT']
COLLECTOR_INSTANCES_CHECK_PORT = CONFIGURATION['COLLECTOR_INSTANCES_CHECK_PORT']
COLLECTOR_HEALTH_CHECK_PORT = CONFIGURATION['COLLECTOR_HEALTH_CHECK_PORT']
COLLECT_TASK_PORT = CONFIGURATION['COLLECT_TASK_PORT']
MONITOR_PORT = CONFIGURATION['MONITOR_PORT']
COLLECT_INTERVAL = CONFIGURATION['COLLECT_INTERVAL']
DISK_PARTITION = CONFIGURATION['DISK_PARTITION']
DAEMON_PORT = CONFIGURATION['DAEMON_PORT']
NUM_DAEMONS = CONFIGURATION['NUM_DAEMONS']

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
