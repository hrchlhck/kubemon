import socket
from ..dataclasses import Client
from typing import List
from kubemon.utils import receive, send_to
from kubemon.config import DATA_PATH, START_MESSAGE, DEFAULT_DAEMON_PORT

import dataclasses
import abc

__all__ = [
    'Command', 
    'COMMANDS'
    'NotExistCommand', 
    'StartCommand', 
    'InstancesCommand', 
    'ConnectedMonitorsCommand',
    'StopCommand',
]

COMMANDS = {
    'StartCommand': 'start <output_dir>', 
    'InstancesCommand': 'instances',
    'ConnectedMonitorsCommand': 'monitors',
    'StopCommand': 'stop'
}

@dataclasses.dataclass
class Command(abc.ABC):
    @abc.abstractmethod
    def execute(self) -> str:
        pass

class StartCommand(Command):
    def __init__(self, instances: List[Client], dir_name: str, addr: str):
        self._instances = instances
        self._dir_name = dir_name
        self._monitor_addr = addr

    def execute(self) -> str:
        if not len(self._instances):
            return "There are no connected monitors to be started"

        for instance in self._instances:
            send_to(instance.socket_obj, START_MESSAGE)
        return f"Starting {len(self._instances)} monitors and saving data at {self._monitor_addr}:{str(DATA_PATH)}/{self._dir_name}"


class InstancesCommand(Command):
    def __init__(self, instances: List[Client]):
        self._instances = instances

    def execute(self) -> str:
        os = list(filter(lambda x: x.name.startswith('OSMonitor'), self._instances))
        docker = list(filter(lambda x: x.name.startswith('DockerMonitor'), self._instances))
        process = list(filter(lambda x: x.name.startswith('ProcessMonitor'), self._instances))
        
        message = f"Total connected instances: {len(self._instances)}\n"
        message += f"\t- OSMonitor instances: {len(os)}\n"
        message += f"\t- DockerMonitor instances: {len(docker)}\n"
        message += f"\t- ProcessMonitor instances: {len(process)}\n"
        return message

class ConnectedMonitorsCommand(Command):
    def __init__(self, instances: List[Client]):
        self._instances = instances
    
    def execute(self) -> str:
        # Filtering only OSMonitor instances
        os = list(filter(lambda x: x.name.startswith('OSMonitor'), self._instances))

        # Parsing hostname and IP address
        os = list(map(lambda x: f"Hostname: {x.name.split('_')[5]}\tIP: {'.'.join(i for i in x.name.split('_')[1:5])}", os))

        message = f"Total OSMonitor instances: {len(os)}\n"
        
        if len(os):
            for monitor in os:
                message += "- " + monitor + "\n"
        return message

class StopCommand(Command):
    def __init__(self, instances: List[Client], daemon_addresses: List[str], is_running: bool):
        self._instances = instances
        self._daemon_addresses = daemon_addresses
        self._is_running = is_running
    
    def execute(self) -> str:
        if not self._is_running:
            return 'Unable to stop idling monitors'
            
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in self._daemon_addresses:
                send_to(sockfd, 'stop', (addr, DEFAULT_DAEMON_PORT))
        
        return f'Stopped {len(self._instances)} instances'

class NotExistCommand(Command):
    def execute(self) -> str:
        return "Command does not exist"
