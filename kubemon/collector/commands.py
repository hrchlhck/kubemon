from kubemon.utils import receive, send_to, is_alive
from kubemon.config import (
    DATA_PATH,
    RESTART_MESSAGE, 
    START_MESSAGE, 
    DEFAULT_DAEMON_PORT,
    STOP_MESSAGE
)

from typing import Dict
from datetime import datetime

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
    def __init__(self, collector):
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

        if not len(collector.instances):
            return "There are no connected monitors to be started.\n"
        
        if not collector.dir_name:
            return "Argument 'dir_name' is missing.\n"

        for instance in collector.instances:
            send_to(instance.socket_obj, START_MESSAGE)
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for daddr in collector.daemons.values():
                send_to(sockfd, 'start', (daddr, DEFAULT_DAEMON_PORT))

        collector.is_running = True
        collector.running_since = datetime.now()

        return f"Starting {collector.connected_instances} monitors and saving data at {collector.address}:{str(DATA_PATH)}/{collector.dir_name}\n"


class InstancesCommand(Command):
    """ Lists all the connected monitor instances.
    """

    def execute(self) -> str:
        collector = self._collector
        message = ""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in collector.daemons.values():
                message += f'Host: {addr}\n\n'
                send_to(sockfd, "instances", (addr, DEFAULT_DAEMON_PORT))
                data, _ = receive(sockfd)
                message += data
            message += f'Total instances connected: {collector.connected_instances}'
        
        if message == "":
            message = "No instances connected yet."

        return message

class IsReadyCommand(Command):
    """ Returns the expected amount of instances that should 
    be connected to the collector.
    """

    def execute(self) -> str:
        collector = self._collector
        total = 0
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in collector.daemons.values():
                send_to(sockfd, "n_monitors", (addr, DEFAULT_DAEMON_PORT))
                n, _ = receive(sockfd)
                total += int(n)

        return collector.connected_instances == total and total != 0 and collector.expected_instances == total

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
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in collector.daemons.values():
                send_to(sockfd, 'stop', (addr, DEFAULT_DAEMON_PORT))

                msg, _ = receive(sockfd)

                collector.logger.debug(f'Received {msg}')
                
                if msg == STOP_MESSAGE:
                    collector.is_running = False
                    collector.running_since = None

        return f'Stopped {collector.connected_instances} instances\n'

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

class IsRunningCommand(Command):
    """ Tells if the monitors are running.
    """
    
    def execute(self) -> str:
        collector = self._collector

        msg = f"Running since: {str(collector.running_since)}\n"
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in collector.daemons.values():
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

    def execute(self) -> bool:
        return is_alive(self._addr, self._port)

class RestartCommand(Command):
    """ Restars the monitor instances
    """

    def execute(self) -> str:
        collector = self._collector
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            for addr in collector.daemons.values():
                collector.logger.debug(f'Sent \'restart\' to {addr}:{DEFAULT_DAEMON_PORT}')
                send_to(sockfd, 'restart', (addr, DEFAULT_DAEMON_PORT))
            
            msg, addr = receive(sockfd)
            
            if msg == RESTART_MESSAGE:
                for addr in collector.daemons.values():
                    instances = [i for i in collector.instances if addr == i.address[0]]

                    for client in instances:
                        collector.logger.debug(f'Closed socket {client.name}@{client.socket_obj.getsockname()}')
                        client.socket_obj.close()

                collector.instances = list()

        return 'Restarted daemons'

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
    '_is_ready': IsReadyCommand,
}