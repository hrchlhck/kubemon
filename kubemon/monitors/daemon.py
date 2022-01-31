from kubemon.log import create_logger
from kubemon.pod import Pod
from kubemon.utils import get_containers, get_container_pid, get_host_ip, is_alive, receive, send_to
from kubemon.monitors.base_monitor import BaseMonitor, MonitorFlag
from kubemon.monitors.commands import COMMAND_CLASSES
from kubemon.config import (
    COLLECTOR_HEALTH_CHECK_PORT, COLLECTOR_INSTANCES_CHECK_PORT, 
    DEFAULT_CLI_PORT, DEFAULT_MONITOR_INTERVAL, 
    DEFAULT_MONITOR_PORT, DEFAULT_DAEMON_PORT, 
    MONITOR_PROBE_INTERVAL
)
from . import (
    OSMonitor, 
    DockerMonitor, 
    ProcessMonitor
)

from typing import List, Tuple
from psutil import Process as psProcess
from docker import from_env
from time import sleep as time_sleep

import threading
import socket
import sys

__all__ = ['Kubemond']

LOGGER = create_logger('daemon')

class Kubemond(threading.Thread):
    """ Kubemon Daemon Class. """

    def __init__(self, address: str, port=DEFAULT_MONITOR_PORT, interval=DEFAULT_MONITOR_INTERVAL, probe_interval=MONITOR_PROBE_INTERVAL):
        self.__address = address
        self.__port = port
        self.__interval = interval
        self.__probe_interval = probe_interval
        self.__is_running = False
        self.__mutex = threading.Lock()
        self.__monitors = []
        self.__directory = None
        self.logger = LOGGER
        threading.Thread.__init__(self)
    
    @property
    def address(self) -> str:
        return self.__address

    @property
    def port(self) -> int:
        return self.__port

    @property
    def interval(self) -> int:
        return self.__interval
    
    @property
    def directory(self) -> str:
        return self.__directory

    @property
    def probe_interval(self) -> int:
        return self.__probe_interval

    @property
    def is_running(self) -> bool:
        return self.__is_running
    
    @is_running.setter
    def is_running(self, val: bool) -> None:
        if isinstance(val, bool):
            self.__is_running = val
        else:
            raise ValueError(f"Must specify a boolean value instead of {type(val)}")
    
    @property
    def monitors(self) -> List[BaseMonitor]:
        return self.__monitors
    
    @monitors.setter
    def monitors(self, val) -> None:
        self.__monitors = val
    
    @property
    def mutex(self) -> threading.Lock:
        return self.__mutex
 
    def listen_commands(self) -> None:
        self.logger.debug("Started listen_commands")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            sockfd.bind(('0.0.0.0', DEFAULT_DAEMON_PORT))
            
            while True:
                # Receive the data
                data, addr = receive(sockfd)

                # Splitting into (command, args)
                cmd, *args = data.split()
                cmd = cmd.lower()

                self.logger.debug(f"Received from {addr}: {data} ({sys.getsizeof(data)} bytes)")

                # Getting the function according to the received command
                command = COMMAND_CLASSES.get(cmd)

                # If it exists, then execute it with the received arguments
                if command:
                    command = command(self, sockfd, addr)
                    self.logger.info(command.execute())
                else:
                    self.logger.info(f"Command '{data}' does not exist")

    def probe_new_instances(self) -> None:
        args = self.address, self.port, self.interval

        while True:
            instances = docker_instances(*args) + process_instances(*args)

            has_changed, new_instances = self.has_changed(instances)

            if has_changed:
                self.monitors += new_instances

                self._start_monitors(new_instances)
            time_sleep(self.probe_interval)

    def _start_monitors(self, instances: List[BaseMonitor]) -> None:
        for monitor in instances:
            if monitor.flag == MonitorFlag.NOT_CONNECTED and not monitor.is_alive():
                monitor.start()

    def _send_num_monitors(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            self.logger.debug('Waiting for collector response')
            send_to(sockfd, '_num_monitors', (self.address, DEFAULT_CLI_PORT))
            # msg, addr = receive(sockfd)

    def _connect_collector(self):
        self.logger.info('Started _connect_collector')
        state = is_alive(self.address, COLLECTOR_HEALTH_CHECK_PORT)

        while not state:
            self.logger.debug('Waiting for collector to be alive')
            time_sleep(2)
            state = is_alive(self.address, COLLECTOR_HEALTH_CHECK_PORT)
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
                sockfd.connect((self.address, COLLECTOR_INSTANCES_CHECK_PORT))
                self.logger.info('Connected to collector')

                name = f'[Daemon] - {socket.gethostname()}'
                address = str(get_host_ip())
                msg = (name, address)

                send_to(sockfd, msg)
                self.logger.debug(f'Sent {msg} to {self.address}:{COLLECTOR_INSTANCES_CHECK_PORT}')

                while True:
                    time_sleep(2)
                    msg = len(self.monitors)
                    send_to(sockfd, msg)
                    self.logger.debug(f'Sent {msg} to {self.address}:{COLLECTOR_INSTANCES_CHECK_PORT}')

    def run(self) -> None:
        self._init_monitors()

        # Create all monitor instances 
        self._start_monitors(self.monitors)

        self.logger.info("Started daemon")

        # Probe if any new container/pod/process has been created
        threading.Thread(target=self.probe_new_instances).start()

        # Keep sending the amount of instances to the collector
        threading.Thread(target=self._connect_collector).start()

        # Listen any incoming commands to redirect to the monitors
        self.listen_commands()
    
    def has_changed(self, new: list) -> Tuple[bool, List[BaseMonitor]]:
        ret = [instance for instance in new if str(instance) not in list(map(str, self.monitors))]
        return len(ret) > 0, ret

    def _init_monitors(self) -> None:
        self.monitors += [OSMonitor(address=self.address, port=self.port, interval=self.interval)]
        self.monitors += docker_instances(self.address, self.port, self.interval)
        self.monitors += process_instances(self.address, self.port, self.interval)

def docker_instances(address: str, port: int, interval: int) -> list:
    monitors = list()
    pods = Pod.list_pods(namespace='*')

    for p in pods:
        for c in p.containers:
            monitor = DockerMonitor(c, p, get_container_pid(c), address=address, port=port, interval=interval)
            monitors.append(monitor)
    
    return monitors

def process_instances(address: str, port: int, interval: int) -> list:
    client = from_env()
    containers = get_containers(client)
    container_pids = [(get_container_pid(c), c) for c in containers]
    monitors = list()

    for pid, container_obj in container_pids:
        process = psProcess(pid=pid)

        for child in process.children():
            monitor = ProcessMonitor(container_obj, child.pid, address=address, port=port, interval=interval)
            monitors.append(monitor)

    return monitors

