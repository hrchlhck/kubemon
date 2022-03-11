from functools import wraps, lru_cache
from typing import Any, Callable, Dict, List
from flask_restful import Resource, Api
from gunicorn.app.base import BaseApplication

from kubemon.dataclasses import Pod
from kubemon.log import create_logger
from kubemon.pod import list_pods
from kubemon.utils.process import get_children_pids, pid_exists
from kubemon.utils.containers import get_containers, get_container_pid
from kubemon.utils.networking import get_host_ip
from kubemon.utils.monitors import list_monitors

from kubemon.settings import (
    MONITOR_PORT,
    K8S_NAMESPACES,
    FROM_K8S,
    Volatile
) 
from . import (
    OSMonitor, 
    DockerMonitor, 
    ProcessMonitor
)

import requests
import psutil
import docker
import flask

__all__ = ['Kubemond']

LOGGER = create_logger('daemon')
APP = flask.Flask(__name__)
API = Api(APP)

def _get_stats(instances: list) -> Dict[str, dict]:
    return {str(i): i.get_stats() for i in instances}

class ROS(Resource):
    def get(self):
        instances = {
           'total': 1,
           'instances': _get_stats([OSMonitor()])
       }
        return flask.make_response(flask.jsonify(instances), 200)

class RDocker(Resource):
    def get(self):
        client = docker.from_env()
        instances = docker_instances(client)
        instances = {
           'total': len(instances),
           'instances': _get_stats(instances)
        }
        return flask.make_response(flask.jsonify(instances), 200)

class RProcess(Resource):
    def get(self):
       client = docker.from_env()
       instances = process_instances(client)
       instances = {
           'total': len(instances),
           'instances': _get_stats(instances)
       }
       return flask.make_response(flask.jsonify(instances), 200)

class RHome(Resource):
    def get(self):
        _MODULES = [DockerMonitor, ProcessMonitor, OSMonitor]
        data = {
            'hostname': str(OSMonitor()),
            'metric_paths': [flask.url_for(i) for i in list_monitors(_MODULES)],
            'total': sum(requests.get(flask.request.base_url + m).json()['total'] for m in list_monitors(_MODULES))
        }
        return flask.jsonify(data)

API.add_resource(RHome, '/')
API.add_resource(ROS, '/os', endpoint='os')
API.add_resource(RDocker, '/docker', endpoint='docker')
API.add_resource(RProcess, '/process', endpoint='process')

class Kubemond(BaseApplication):
    """ Kubemon Daemon Class. """

    def __init__(self, app=APP, port=MONITOR_PORT):
        Volatile.set_procfs(psutil.__name__)
        self.__port = port
        self.app = app
        self.logger = LOGGER
        self.options = {
                'workers': 4,
                'bind': f'{get_host_ip()}:{port}'
        }
        super().__init__()
    
    @property
    def port(self) -> int:
        return self.__port

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}

        for k, v in config.items():
            self.cfg.set(k.lower(), v)

    def load(self):
        return self.app
    
    def start(self):
        self.run()

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

@lru_cache
@client_error
def docker_instances(client: docker.client.DockerClient) -> List[DockerMonitor]:   
    to_monitor = lambda c: DockerMonitor(c.container) if isinstance(c, Pod) else DockerMonitor(c)

    pods = list_pods(*K8S_NAMESPACES, client=client, from_k8s=FROM_K8S)

    return list(map(to_monitor, pods))

@lru_cache
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

