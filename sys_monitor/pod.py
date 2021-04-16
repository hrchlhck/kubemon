from pathlib import Path
from docker.models.containers import Container
from typing import List, NamedTuple
from collections import namedtuple, deque
from subprocess import check_output
import re
import docker
import os
import sys

__all__ = ['Pod', 'Pair']

Pair = namedtuple('Pair', ['name', 'id'])


def get_container_name_by_id(container_id: str):
    """ Get container name by an given id. """
    if isinstance(container_id, str):
        cmd = "docker inspect -f {{.Name}} %s" % container_id
        ret = check_output(cmd.split()).decode("utf8")

        # Remove junk characters
        for char in "/\n":
            ret = ret.replace(char, "")

        return ret
    else:
        raise ValueError("Object of type %s is not a container" %
                         type(container))


def parse_container_id(container_id: str):
    """ Parse container ID from cgroups directory """
    pattern = ".-"
    if any(c for c in pattern if c in container_id):
        return re.split("[.-]", container_id)[1]
    return container_id


class Pod:
    """ Class to represent (simply) a Pod object from Kubernetes """

    def __init__(self, name: str, uid: str, containers: List[Container]=list()):
        self.__name = name
        self.__id = uid
        self.__containers = containers

    @property
    def name(self) -> str:
        return self.__name

    @property
    def id(self) -> str:
        return self.__id

    @property
    def containers(self) -> List[Container]:
        return self.__containers
    
    @containers.setter
    def containers(self, other: List[Container]) -> None:
        self.__containers = other
    
    def path(self, controller: str, qos="besteffort") -> str:
        """ 
        Returns the path of the pod on a cgroup controller 
        
        Args:
            controller (str): cgroup controller
            qos (str): QoS class from Kubernetes
        
        """
        return f"/sys/fs/cgroup/{controller}/kubepods/{qos}/pod{self.id}"

    def __repr__(self):
        return "Pod<Name=%s, id=%s, containers=%s>" % (self.name, self.id, self.containers)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def parse_pod_name(container_name: str) -> object:
        """ 
        Parses pod names based Kubernetes naming pattern.

        Args:
            container_name (str): Container name 
        """
        pattern = r"([a-f-0-9]){8}-([a-f-0-9]){4}-([a-f-0-9]){4}-([a-f-0-9]){4}-([a-f-0-9]){12}"
        pod_id = re.search(pattern, container_name).group()
        return Pod(container_name, uid=pod_id)

    @staticmethod
    def list_pods(namespace="default", controller='systemd', qos="besteffort") -> list:
        """ 
        List containers within the pod on cgroups.

        Args:
            namespace (str): Avoid the given namespace
            controller (str): cgroup controller
            qos (str): QoS class from kubernetes
        """
        if sys.platform.startswith("win"):
            raise OSError("Current operating system not supported")

        path = f"/sys/fs/cgroup/{controller}/kubepods/{qos}/"

        client = docker.from_env()

        # Get containers that arent pods
        containers = [c for c in client.containers.list() if 'POD' not in c.name]

        # Get containers that are pods
        pods = [c for c in client.containers.list() if 'POD' in c.name]

        # Get all pods from all namespaces except kube-system
        if namespace == '*':
            containers = [c for c in containers if 'kube-system' not in c.name]
            pods = [c for c in pods if 'kube-system' not in c.name]
        else:
            containers = [c for c in containers if namespace in c.name]
            pods = [c for c in pods if namespace in c.name]

        # Map container names and container IDs
        containers = [Pair(c.name, c.id) for c in containers]

        # Map containers into pod objects
        pods = [Pod.parse_pod_name(pod.name) for pod in pods]
        
        # Filter pod container from cgroups dir
        for pod in pods:           
            filtered_containers = [c for c in containers if c.id in os.listdir(pod.path(controller, qos=qos))]

            pod.containers = filtered_containers

        return pods
