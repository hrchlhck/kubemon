from kubemon.config import RESTART_MESSAGE, STOP_MESSAGE
from kubemon.utils import receive, send_to
from kubemon.monitors import OSMonitor, DockerMonitor, ProcessMonitor
from kubemon.monitors.base_monitor import MonitorFlag

from typing import Tuple

import dataclasses
import abc
import socket
import time


@dataclasses.dataclass
class Command:
    def __init__(self, daemon, sockfd: socket.socket, addr: Tuple[str, int]):
        self._daemon = daemon
        self._sockfd = sockfd
        self._addr = addr
        self._log = daemon.logger
    
    @abc.abstractmethod
    def execute(self) -> str:
        pass

class StartCommand(Command):
    def execute(self) -> str:
        self._daemon.is_running = True
        return 'Started modules'

class StopCommand(Command):
    def execute(self) -> str:
        running_instances = [instance for instance in self._daemon.monitors if instance.flag == MonitorFlag.RUNNING]

        if not running_instances:
            self._log.info("There are no monitors running")
            return

        for monitor in running_instances:
            self._daemon.mutex.acquire()
            monitor.stop_request = True
            self._log.info(f"Stopping {monitor}")
            self._daemon.mutex.release()
        
        self._daemon.is_running = False

        send_to(self._sockfd, STOP_MESSAGE, self._addr)

        return 'Stopped modules'

class IsRunningCommand(Command):
    def execute(self) -> str:
        msg = 'Is running?: '
        msg += 'Yes' if self._daemon.is_running else 'No'
        msg += '\n'
        send_to(self._sockfd, msg, self._addr)

        return f'Sent \'{msg}\' to {self._addr}'

class NumMonitorsCommand(Command):
    def execute(self) -> str:
        n_monitors = f'{len(self._daemon.monitors)}\n'
        send_to(self._sockfd, n_monitors, self._addr)
        return f'Sent \'{n_monitors}\' to {self._addr}'

class RestartCommand(Command):
    def execute(self) -> str:
        monitors = [m for m in self._daemon.monitors if m.flag != MonitorFlag.NEVER_STARTED]
        for monitor in monitors:
            while monitor.flag is not MonitorFlag.STOPPED:
                self._log.info(f'Waiting for {monitor} to be stopped')
                time.sleep(2)
                
        send_to(self._sockfd, RESTART_MESSAGE, self._addr)

        self._daemon.monitors = list()
        self._daemon._init_monitors()
        self._daemon._start_monitors(self._daemon.monitors)

        send_to(self._sockfd, len(self._daemon.monitors), self._addr)

        return 'Restarted'

class ListInstancesCommand(Command):
    def execute(self) -> str:
        msg = ""
        monitor_per_class = {
            'OS': [m for m in self._daemon.monitors if isinstance(m, OSMonitor)], 
            'Process': [m for m in self._daemon.monitors if isinstance(m, ProcessMonitor)], 
            'Docker': [m for m in self._daemon.monitors if isinstance(m, DockerMonitor)]
        }

        for klass, instances in monitor_per_class.items():
            msg += klass + ' - ' + str(len(monitor_per_class[klass])) + '\n\t'
            msg += '\n\t'.join([str(i) for i in instances]) + '\n'
            msg += '\n'
        send_to(self._sockfd, msg, self._addr)
        return f'Sent \'{msg}\' to {self._addr}'

COMMAND_CLASSES = {
    'start': StartCommand,
    'stop': StopCommand,
    'running': IsRunningCommand,
    'instances': ListInstancesCommand,
    'n_monitors': NumMonitorsCommand,
    'restart': RestartCommand,
}