from ..dataclasses import Client
from typing import Dict, List
from kubemon.utils import receive, send_to, is_alive

from kubemon.config import (
    DATA_PATH, 
    START_MESSAGE, 
    DEFAULT_DAEMON_PORT
)

import dataclasses
import socket
import abc

__all__ = [
    'Command', 
    'COMMANDS'
    'NotExistCommand', 
    'StartCommand', 
    'InstancesCommand', 
    'ConnectedDaemonsCommand',
    'StopCommand',
    'HelpCommand'
]

COMMANDS = {
    'StartCommand': 'start <output_dir>', 
    'InstancesCommand': 'instances',
    'ConnectedDaemonsCommand': 'daemons',
    'StopCommand': 'stop',
}

@dataclasses.dataclass
class Command(abc.ABC):
    @abc.abstractmethod
    def execute(self) -> str:
        pass

class StartCommand(Command):
    """ Start collecting metrics from all connected daemons in the collector.

    Args:
        - Directory name to be saving the data collected. Ex.: start test000
    """

    def __init__(self, instances: List[Client], daemons: List[str], dir_name: str, addr: str):
        self._instances = instances
        self._dir_name = dir_name
        self._monitor_addr = addr
        self._daemons = daemons

    def execute(self) -> str:
        if not len(self._instances):
            return "There are no connected monitors to be started\n"

        for instance in self._instances:
            send_to(instance.socket_obj, START_MESSAGE)
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for daddr in self._daemons:
                send_to(sockfd, 'start', (daddr, DEFAULT_DAEMON_PORT))

        return f"Starting {len(self._instances)} monitors and saving data at {self._monitor_addr}:{str(DATA_PATH)}/{self._dir_name}\n"


class InstancesCommand(Command):
    """ Lists all the connected monitor instances.
    """

    def __init__(self, daemons: List[str]):
        self._daemons = daemons

    def execute(self) -> str:
        message = ""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in self._daemons:
                message += f'Host: {addr}\n\n'
                send_to(sockfd, "instances", (addr, DEFAULT_DAEMON_PORT))
                data, _ = receive(sockfd)
                message += data
        
        if message == "":
            message = "No instances connected yet."

        return message

class ConnectedDaemonsCommand(Command):
    """ Lists all the daemons (hosts) connected.
    """

    def __init__(self, instances: List[Client]):
        self._instances = instances
    
    def execute(self) -> str:
        # Filtering only OSMonitor instances
        os = list(filter(lambda x: x.name.startswith('OSMonitor'), self._instances))

        # Parsing hostname and IP address
        os = list(map(lambda x: f"Hostname: {x.name.split('_')[5]} | IP: {'.'.join(i for i in x.name.split('_')[1:5])}", os))

        message = f"Total daemons connected: {len(os)}\n"
        
        if len(os):
            for monitor in os:
                message += "- " + monitor + "\n"
        return message

class StopCommand(Command):
    """ Stop all monitors if they're running.
    """

    def __init__(self, instances: List[Client], daemon_addresses: List[str], is_running: bool):
        self._instances = instances
        self._daemon_addresses = daemon_addresses
        self._is_running = is_running
    
    def execute(self) -> str:
        # if not self._is_running:
        #     return 'Unable to stop idling monitors\n'
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in self._daemon_addresses:
                send_to(sockfd, 'stop', (addr, DEFAULT_DAEMON_PORT))
        
        return f'Stopped {len(self._instances)} instances\n'

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
            msg += f'\'{key}\':'
            msg += value.__doc__ + '\n'
        
        return msg

class IsRunningCommand(Command):
    """ Tells if the monitors are running.
    """

    def __init__(self, daemons: List[str], since: str):
        self._daemons = daemons
        self._since = since
    
    def execute(self) -> str:
        
        msg = f"Running since: {str(self._since)}\n"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in self._daemons:
                send_to(sockfd, 'running', (addr, DEFAULT_DAEMON_PORT))
                data, _ = receive(sockfd)
                msg += addr + " - " + data

        return msg + '\n'

class IsAliveCommand(Command):
    """ Tells if the collector is alive.
    """
    def __init__(self, address: str, port: int):
        self._addr = address
        self._port = port

    def execute(self) -> str:
        alive, sockfd = is_alive(self._addr, self._port)

        msg = 'Collector is offline.'

        if alive and sockfd:
            print('Ping')
            msg, _ = receive(sockfd)
            sockfd.close()

        return msg

class RestartCommand(Command):
    """ Restars the monitor instances
    """

    def __init__(self, daemons: List[str]):
        self._daemons = daemons

    def execute(self) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in self._daemons:
                send_to(sockfd, 'restart', (addr, DEFAULT_DAEMON_PORT))
        return super().execute()

COMMAND_CLASSES = {
    'start': StartCommand,
    'instances': InstancesCommand,
    'daemons': ConnectedDaemonsCommand,
    'stop': StopCommand,
    'not exist': NotExistCommand,
    'help': HelpCommand,
    'is_running': IsRunningCommand,
    'is_alive': IsAliveCommand,
    'restart': RestartCommand,
}