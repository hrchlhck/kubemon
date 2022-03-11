from kubemon.utils.networking import send_to, is_alive
from kubemon.settings import DATA_PATH, MONITOR_PORT, START_MESSAGE, Volatile

from typing import Dict
from datetime import datetime
from functools import lru_cache, wraps

import time
import requests
import abc

def newline_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        if not isinstance(ret, str):
            return str(ret) + '\n'
        return ret
    return wrapper


class Command(abc.ABC):
    def __init__(self, collector,):
        self._collector = collector
    
    @abc.abstractmethod
    def execute(self) -> str:
        pass

class StartCommand(Command):
    """ Start collecting metrics from all connected daemons in the collector.

    Args:
        - Directory name to be saving the data collected. Ex.: start test000
    """

    @newline_decorator
    def execute(self) -> str:
        collector = self._collector
        
        if not collector.dir_name:
            return "Argument 'dir_name' is missing."

        # Check if the number of daemons connected to collector 
        # are the number expected by Volatile.NUM_DAEMONS
        if Volatile.NUM_DAEMONS != len(collector):
            return f"{Volatile.NUM_DAEMONS} daemon(s) expected. There are connected only {len(collector)}."

        for sockfd in collector._monitor_sockets:
            send_to(sockfd, START_MESSAGE)

        with collector.mutex:
            collector.is_running = True

        collector.running_since = datetime.now()

        return f"Starting {len(collector)} daemons and saving data at {collector.address}:{str(DATA_PATH)}/{collector.dir_name}"


class InstancesCommand(Command):
    """ Lists all the connected monitor instances.
    """

    def _instances_per_daemon(self, module: str, url: str) -> str:
        req = requests.get(url + module)

        if req.status_code != 200:
            return ''
        return req.json()['total']

    @lru_cache
    @newline_decorator
    def execute(self) -> str:
        collector = self._collector
        message = ""
        port = MONITOR_PORT
        
        total = 0
        start_time = time.time()
        
        with collector.mutex:
            for hostname, addr in collector.daemons.items():
                url = f'http://{addr}:{port}'
                req = requests.get(url)

                if req.status_code != 200:
                    continue

                req = req.json()

                instances_per_module = {module: self._instances_per_daemon(module, url) for module in req['metric_paths']}
                total_per_daemon = sum(i for i in instances_per_module.values())
                total += req['total']
                message += f'Instances in {hostname}@{addr}: {total_per_daemon}\n'

                # Listing number of instances per module, per daemon
                for module, n_inst in instances_per_module.items():
                    name = module.upper().replace('/', '')
                    message += f'\t - {name}: {n_inst}\n'

        message += f'Total instances: {total}'  
        end_time = time.time()

        message += f'\nTotal processing time: {end_time - start_time:.3f}s'

        return message

class IsReadyCommand(Command):
    """ Returns the expected amount of instances that should 
    be connected to the collector.
    """

    @newline_decorator
    def execute(self) -> str:
        from kubemon.settings import Volatile
        
        collector = self._collector

        return not collector.stop_request and len(collector) == Volatile.NUM_DAEMONS

class ConnectedDaemonsCommand(Command):
    """ Lists all the daemons (hosts) connected.
    """
    
    @newline_decorator
    def execute(self) -> str:
        collector = self._collector

        daemons = collector.daemons

        message = f"Total daemons connected: {len(daemons)}\n"
        
        if len(daemons):
            for name, addr in daemons.items():
                message += "- " + name + " | " + addr + "\n"
        return message

class StopCommand(Command):
    """ Stop all monitors if they're running.
    """
    
    @newline_decorator
    def execute(self) -> str:
        collector = self._collector
        
        if not collector.is_running:
            return 'Collector isn\'t running to be stopped.'

        with collector.mutex:
            collector.stop_request = True
        
        # Release all the monitors from the barrier
        for _ in range(Volatile.NUM_DAEMONS):
            collector.barrier.acquire()

        # Resetting the collector status
        with collector.mutex:
            collector.stop_request = False
            collector.is_running = False

        return 'Stopped collector'

class NotExistCommand(Command):
    """ Indicates if a command does not exist. 
    """

    @newline_decorator
    def execute(self) -> str:
        return "Command does not exist"

class HelpCommand(Command):
    """ Lists all the available commands.
    """
    def __init__(self, command_dict: Dict[str, Command]):
        self._cmd_dict = command_dict
    
    @newline_decorator
    def execute(self) -> str:
        msg = ""

        for key, value in self._cmd_dict.items():
            # Ignoring dunder commands
            if not key.startswith('_'):
                msg += f'\'{key}\':'
                msg += value.__doc__ + '\n'
        
        return msg

class IsAliveCommand(Command):
    """ Tells if the collector is alive.
    """
    def __init__(self, address: str, port: int):
        self._addr = address
        self._port = port

    def execute(self) -> bool:
        return is_alive(self._addr, self._port)

COMMAND_CLASSES = {
    'start': StartCommand,
    'instances': InstancesCommand,
    'daemons': ConnectedDaemonsCommand,
    'stop': StopCommand,
    'not exist': NotExistCommand,
    'help': HelpCommand,
    'alive': IsAliveCommand,
    '_is_ready': IsReadyCommand,
}