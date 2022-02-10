from kubemon.log import create_logger
from kubemon.pod import Pod
from kubemon.utils import (
    get_children_pids, 
    get_containers, 
    get_container_pid, 
    get_host_ip, 
    is_alive, 
    receive,
    send_to
)
from kubemon.config import (
    MONITOR_PORT,
    COLLECTOR_HEALTH_CHECK_PORT,
    COLLECTOR_INSTANCES_CHECK_PORT,
    DAEMON_PORT,

) 
from . import (
    OSMonitor, 
    DockerMonitor, 
    ProcessMonitor
)

from psutil import pid_exists
from docker import from_env
from time import sleep as time_sleep

import threading
import socket
import sys
import flask

__all__ = ['Kubemond']

LOGGER = create_logger('daemon')
APP = flask.Flask(__name__)

class Kubemond(threading.Thread):
    """ Kubemon Daemon Class. """

    def __init__(self, address: str, port=MONITOR_PORT):
        self.__address = address
        self.__port = port
        self.__mutex = threading.Lock()
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
    def directory(self) -> str:
        return self.__directory
    
    @property
    def mutex(self) -> threading.Lock:
        return self.__mutex

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

                name = socket.gethostname()
                address = str(get_host_ip())
                msg = (name, address)

                send_to(sockfd, msg)
                self.logger.debug(f'Sent {msg} to {self.address}:{COLLECTOR_INSTANCES_CHECK_PORT}')

    def run(self) -> None:
        # Send to collector the daemon name and IP
        self._connect_collector()

        APP.run(host=get_host_ip(), port=self.port)

    @staticmethod
    @APP.route('/')
    def _init_monitors() -> None:
        instances = docker_instances() + process_instances() + [OSMonitor()]
        
        instances = {str(i): i.get_stats() for i in instances}

        return flask.jsonify(instances)

def docker_instances() -> list:
    monitors = list()
    pods = Pod.list_pods(namespace='*')

    for p in pods:
        for c in p.containers:
            monitor = DockerMonitor(c, p, get_container_pid(c))
            monitors.append(monitor)
    
    return monitors

def process_instances() -> list:
    client = from_env()
    containers = get_containers(client)
    container_pids = [(get_container_pid(c), c) for c in containers]
    monitors = list()

    for pid, container_obj in container_pids:
        for cpid in get_children_pids(pid):
            if pid_exists(cpid):
                monitor = ProcessMonitor(container_obj, cpid)
                monitors.append(monitor)

    return monitors

