from pathlib import Path
from functools import lru_cache
from docker.models.containers import Container
from typing import List, NamedTuple
from collections import namedtuple
from subprocess import check_output
from re import split as _split
import os
import sys

__all__ = ['Pod', 'Pair']

Pair = namedtuple('Pair', ['container', 'name', 'id'])

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
        raise ValueError("Object of type %s is not a container" % type(container))

def parse_container_id(container_id: str):
    """ Parse container ID from cgroups directory """
    return _split("[.-]", container_id)[1]

class Pod:
    """ Class to represent (simply) a Pod object from Kubernetes """
    def __init__(self, name, _id, namespace):
        self.__name = name
        self.__id = _id
        self.__namespace = namespace
    
    @property
    def name(self):
        return self.__name
    
    @property
    def id(self):
        return self.__id
    
    @property
    def namespace(self):
        return self.__namespace

    def __repr__(self):
        return "Pod<Name=%s, id=%s, namespace=%s>" % (self.name, self.id, self.namespace)
    
    def __str__(self):
        return self.__repr__()    

    @staticmethod
    def parse_pod_name(container=None):
        """ 
        Parses pod names based Kubernetes naming pattern.

        Args:
            container (Container): Container object 
        """
        if isinstance(container, Container) or isinstance(container, Pod): 
            slices = container.name.split("_")
        else:
            raise ValueError("Object of type %s is not a pod or container" % type(container))
        pod_id = slices[4].replace("-", "_")
        pod_namespace = slices[3]
        return Pod(container.name, pod_id, pod_namespace)

    @staticmethod
    @lru_cache(maxsize=32)
    def list_pods(client, namespace='') -> List[Container]:
        """ 
        List all running pods on Kubernetes as docker containers. 

        Args:
            client (docker.client.DockerClient): Docker client object
            namespace (str): Pod namespace
        """
        containers = client.containers.list()
        return [Pod.parse_pod_name(pod) for pod in containers if 'POD' in pod.name and namespace in pod.name]

    @staticmethod
    @lru_cache(maxsize=32)
    def list_containers_cgroups(cgroup_controller, **kwargs) -> dict:
        """ 
        List containers within the pod on cgroups.
        
        Args:
            client (docker.client.DockerClient): Docker client object
            namespace (str): Pod namespace
            cgroup_controller (str): Cgroup controller. To see all available controlers, 
            please refer to https://www.man7.org/linux/man-pages/man7/cgroups.7.html

        Returns:
            Dictionary where the key is the pod name and the value are the containers within the pod
            E.g.
                >>> {'pod1': [Pair(container=<Container object 1>, name='container1', id='container1')], ...}
        """
        if sys.platform.startswith("win"):
            raise OSError("Current operating system not supported")
        
        def map_func(container_id: str):
            container_id = parse_container_id(container_id)
            container_obj = kwargs.get("client").containers.get(container_id)
            container_name = get_container_name_by_id(container_id)
            return Pair(container_obj, container_name, container_id)
        
        pods = Pod.list_pods(**kwargs) 
        ret = {}
        for pod in pods:
            pod_path = Path("/sys/fs/cgroup/%s/kubepods.slice/kubepods-besteffort.slice/kubepods-besteffort-pod%s.slice/" % (cgroup_controller, pod.id))

            container_filter = filter(lambda x: x.startswith("docker"), os.listdir(pod_path))

            # Avoiding containers that the name contains `sys` and `POD`
            containers = list(filter(lambda pair: 'POD' not in pair.name and 'sys' not in pair.name, map(map_func, container_filter)))

            ret[Pod.parse_pod_name(pod)] = containers

        return ret

