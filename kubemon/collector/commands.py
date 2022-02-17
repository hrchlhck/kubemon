from kubemon.utils import send_to, is_alive
from kubemon.settings import DATA_PATH, MONITOR_PORT, START_MESSAGE
from typing import Dict
from datetime import datetime

import dataclasses
import requests
import abc

@dataclasses.dataclass
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

    def execute(self) -> str:
        collector = self._collector

        # if not len(collector.instances):
        #     return "There are no connected monitors to be started.\n"
        
        if not collector.dir_name:
            return "Argument 'dir_name' is missing.\n"

        for instance in collector.collector_sockets:
            sock = collector.collector_sockets[instance]
            send_to(sock, START_MESSAGE)

        collector.running_since = datetime.now()

        return f"Starting {len(collector)} daemons and saving data at {collector.address}:{str(DATA_PATH)}/{collector.dir_name}\n"


class InstancesCommand(Command):
    """ Lists all the connected monitor instances.
    """

    def execute(self) -> str:
        collector = self._collector
        message = ""
        port = MONITOR_PORT
        
        total = 0
        for hostname, addr in collector.daemons.items():
            req = requests.get(f'http://{addr}:{port}').json()
            total += len(req)
            message += f'Instances in {hostname}@{addr}: {len(req)}\n'

        message += f'Total instances: {total}'  

        return message

class IsReadyCommand(Command):
    """ Returns the expected amount of instances that should 
    be connected to the collector.
    """

    def execute(self) -> str:
        from kubemon.settings import Volatile
        
        collector = self._collector
        collector.logger.info(collector.collect_status)

        return not collector.stop_request and len(collector) == Volatile.NUM_DAEMONS

class ConnectedDaemonsCommand(Command):
    """ Lists all the daemons (hosts) connected.
    """
    
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
    
    def execute(self) -> str:
        collector = self._collector
        
        with collector.mutex:
            collector.stop_request = True
        
        collector.event.wait()

        return 'Stopped collector\n'

class NotExistCommand(Command):
    """ Indicates if a command does not exist. 
    """

    def execute(self) -> str:
        return "Command does not exist\n"

class HelpCommand(Command):
    """ Lists all the available commands.
    """
    def __init__(self, command_dict: Dict[str, Command]):
        self._cmd_dict = command_dict
    
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

class RestartCommand(Command):
    """ Restars the monitor instances
    """

    def execute(self) -> str:
        collector = self._collector
        
        with collector.mutex:
            collector.stop_request = False

        return 'Restarted collector\n'

COMMAND_CLASSES = {
    'start': StartCommand,
    'instances': InstancesCommand,
    'daemons': ConnectedDaemonsCommand,
    'stop': StopCommand,
    'not exist': NotExistCommand,
    'help': HelpCommand,
    'alive': IsAliveCommand,
    'restart': RestartCommand,
    '_is_ready': IsReadyCommand,
}