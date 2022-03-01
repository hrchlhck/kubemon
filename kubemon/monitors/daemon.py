from functools import wraps
from typing import Any, Callable, Dict, List

from kubemon.dataclasses import Pod
from kubemon.log import create_logger
from kubemon.pod import list_pods
from kubemon.utils.process import get_children_pids, pid_exists
from kubemon.utils.containers import get_containers, get_container_pid
from kubemon.utils.networking import get_host_ip
from kubemon.utils.monitors import list_monitors

from kubemon.settings import (
    MONITOR_PORT,
    Volatile
) 
from . import (
    OSMonitor, 
    DockerMonitor, 
    ProcessMonitor
)

import psutil
import docker
import threading
import socket
import flask

__all__ = ['Kubemond']

LOGGER = create_logger('daemon')
APP = flask.Flask(__name__)

class Kubemond(threading.Thread):
    """ Kubemon Daemon Class. """

    def __init__(self, address: str, port=MONITOR_PORT):
        Volatile.set_procfs(psutil.__name__)

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

    @staticmethod
    def _jsonify(instances: list) -> Dict[str, dict]:
        instances = {str(i): i.get_stats() for i in instances}

        return flask.jsonify(instances)

    def run(self) -> None:
        APP.run(host=get_host_ip(), port=self.port)

    @staticmethod
    @APP.route('/')
    def _init_monitors() -> None:
        _MODULES = [DockerMonitor, ProcessMonitor, OSMonitor]
        data = {
            'hostname': str(OSMonitor()),
            'metric_paths': ['/' + i for i in list_monitors(_MODULES)],
        }
        return flask.jsonify(data)
    
    @staticmethod
    @APP.route('/docker')
    def _docker_instances() -> dict:
        client = docker.from_env()
        instances = docker_instances(client)
        return Kubemond._jsonify(instances)
    
    @staticmethod
    @APP.route('/process')
    def _process_instances() -> dict:
        client = docker.from_env()
        instances = process_instances(client)
        return Kubemond._jsonify(instances)
    
    @staticmethod
    @APP.route('/os')
    def _os_instance() -> dict:
        return Kubemond._jsonify([OSMonitor()])


def client_error(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        if not len(args):
            raise ValueError('Missing argument \'client\'')

        client = args[0]
        if not isinstance(client, docker.client.DockerClient):
            raise TypeError(f'Must specify the DockerClient object instead of \'{type(client).__name__}\'')

        ret = func(*args, **kwargs)
        return ret
    return wrapper

@client_error
def docker_instances(client: docker.client.DockerClient) -> List[DockerMonitor]:   
    to_monitor = lambda c: DockerMonitor(c.container) if isinstance(c, Pod) else DockerMonitor(c)

    pods = list_pods(client=client, from_k8s=False)

    return list(map(to_monitor, pods))    

@client_error
def process_instances(client: docker.client.DockerClient) -> List[ProcessMonitor]:
    containers = get_containers(client)
    container_pids = [(get_container_pid(c), c) for c in containers]
    monitors = list()

    for pid, container_obj in container_pids:
        for cpid in get_children_pids(pid):
            if pid_exists(cpid):
                monitor = ProcessMonitor(container_obj, cpid)
                monitors.append(monitor)

    return monitors

