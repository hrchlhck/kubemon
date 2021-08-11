from ..dataclasses import Client
from typing import List
from kubemon.utils import send_to
from kubemon.config import ROOT_DIR, START_MESSAGE
import dataclasses
import abc

__all__ = ['StartCommand', 'InstancesCommand', 'NotExistCommand', 'Command', 'COMMANDS']

COMMANDS = {
    'StartCommand': '/start <output_dir>', 
    'InstancesCommand': '/instances',
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
        return f"Starting {len(self._instances)} monitors and saving data at {self._monitor_addr}:{ROOT_DIR}/{self._dir_name}"


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

class NotExistCommand(Command):
    def execute(self) -> str:
        return "Command does not exist"
