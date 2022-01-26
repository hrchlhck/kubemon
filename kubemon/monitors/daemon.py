from kubemon.pod import Pod
from kubemon.utils import get_container_pid, receive, send_to
from kubemon.monitors.base_monitor import BaseMonitor, MonitorFlag

from typing import Any, List, Tuple

from ..config import (
    DEFAULT_MONITOR_INTERVAL, 
    DEFAULT_MONITOR_PORT, DEFAULT_DAEMON_PORT,
    MONITOR_PROBE_INTERVAL
)

from . import (
    OSMonitor, 
    DockerMonitor, 
    ProcessMonitor
)

from psutil import Process as psProcess
from ..utils import get_containers, receive
from docker import from_env
from time import sleep as time_sleep

import threading
import socket
import sys

__all__ = ['Kubemond']

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
        self.__functions = {
            'start': self.start_modules,
            'stop': self.stop_modules,
            'running': self.running,
            'instances': self.list_instances,
            'n_monitors': self.num_monitors,
        }
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
        print("Started listen_commands")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            sockfd.bind(('0.0.0.0', DEFAULT_DAEMON_PORT))
            
            while True:
                # Receive the data
                data, addr = receive(sockfd)

                # Splitting into (command, args)
                cmd, *args = data.split()
                cmd = cmd.lower()

                print(f"Received from {addr}: {data} ({sys.getsizeof(data)} bytes)", file=sys.stdout)

                # Getting the function according to the received command
                ret = self.__functions.get(cmd)

                # If it exists, then execute it with the received arguments
                if ret != None:
                    if cmd == 'instances' or cmd == 'running' or cmd == 'n_monitors':
                        ret(sockfd, addr)
                    else:
                        ret(*args)
                else:
                    print(f"Command '{data}' does not exist")

    def num_monitors(self, sockfd: socket.socket, addr: tuple) -> None:
        n_monitors = f'{len(self.monitors)}\n'
        send_to(sockfd, n_monitors, addr)

    def running(self, sockfd: socket.socket, addr: tuple) -> None:
        msg = 'Is running?: '
        msg += 'Yes' if self.is_running else 'No'
        msg += '\n'
        send_to(sockfd, msg, addr)

    def list_instances(self, sockfd: socket.socket, addr: tuple) -> None:
        msg = ""
        monitor_per_class = {
            'OS': [m for m in self.monitors if isinstance(m, OSMonitor)], 
            'Process': [m for m in self.monitors if isinstance(m, ProcessMonitor)], 
            'Docker': [m for m in self.monitors if isinstance(m, DockerMonitor)]
        }

        for klass, instances in monitor_per_class.items():
            msg += klass + ' - ' + str(len(monitor_per_class[klass])) + '\n\t'
            msg += '\n\t'.join([str(i) for i in instances]) + '\n'
            msg += '\n'
        send_to(sockfd, msg, addr)

    def start_modules(self, *args) -> Any:
        print("Called start_modules")
        self.is_running = True

    def stop_modules(self, *args) -> None:
        print("Called stop_modules")

        running_instances = [instance for instance in self.monitors if instance.flag == MonitorFlag.RUNNING]

        if not running_instances:
            print("There are no monitors running")
            return

        for monitor in running_instances:
            self.mutex.acquire()
            monitor.flag = MonitorFlag.IDLE
            monitor.stop_request = True
            print("Stopping ", monitor)
            self.mutex.release()
        
        self.is_running = False

    def probe_new_instances(self) -> None:
        args = self.address, self.port, self.interval

        while True:
            time_sleep(self.probe_interval)
            instances = docker_instances(*args) + process_instances(*args)

            has_changed, new_instances = self.has_changed(instances)

            if has_changed:
                self.monitors += new_instances

                for monitor in new_instances:
                    if monitor.flag == MonitorFlag.NOT_CONNECTED and not monitor.is_alive():
                        monitor.start()

    def run(self) -> None:
        self.__init_monitors()

        print("Started daemon")

        # Create all monitor instances 
        for monitor in self.monitors:
            if monitor.flag == MonitorFlag.NOT_CONNECTED:
                monitor.start()
            else:
                print(f"Monitor {monitor} already connected to collector")

        # Probe if any new container/pod/process has been created
        threading.Thread(target=self.probe_new_instances).start()

        # Listen any incoming commands to redirect to the monitors
        self.listen_commands()
    
    def has_changed(self, new: list) -> Tuple[bool, List[BaseMonitor]]:
        ret = [instance for instance in new if str(instance) not in list(map(str, self.monitors))]
        return len(ret) > 0, ret

    def __init_monitors(self) -> None:
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

