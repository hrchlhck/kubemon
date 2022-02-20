from docker.models.containers import Container
from docker.client import DockerClient, ContainerCollection

from typing import Any, List

from kubemon.dataclasses import Pair

import json

__all__ = ['get_container_pid', 'get_container_name']

def _is_container_or_str(container: Any) -> bool:
    return isinstance(container, Container) or isinstance(container, str)

def get_container_pid(container: Container) -> str:
    if not _is_container_or_str(container):
        raise TypeError('Argument must be of type docker.models.containers.Container or str')

    if isinstance(container, Container):
        path = f'/var/lib/docker/containers/{container.id}/config.v2.json'
    else:
        path = f'/var/lib/docker/containers/{container}/config.v2.json'

    with open(path, 'r') as fp:
        data = fp.read()
    data = json.loads(data)
    return data['State']['Pid']

def get_container_name(container: Container) -> str:
    if not _is_container_or_str(container):
        raise TypeError('Argument must be of type docker.models.containers.Container or str')

    if isinstance(container, Container):
        path = f'/var/lib/docker/containers/{container.id}/config.v2.json'
    else:
        path = f'/var/lib/docker/containers/{container}/config.v2.json'

    with open(path, 'r') as fp:
        data = fp.read()

    data = json.loads(data)

    name = data['Name']

    return name

def get_containers(client: DockerClient, namespace='', to_tuple=False) -> List[ContainerCollection]:
    """ 
    Returns a list of containers. 
        By default and for my research purpose I'm using Kubernetes, so I'm avoiding containers that
        contains 'POD' (created by Kuberenetes) and 'k8s-bigdata' (Namespace in Kubernetes that I've created) 
        in their name. Furthermore I assume that this filter is only applied when the platform is Linux-based, 
        because I've created a Kubernetes cluster only in Linux-based machines, otherwise, if the platform
        is Windows or MacOS, the function will return all containers that are running.

    Args:
        client (DockerClient): Object returned by docker.from_env()
        namespace (str): Used to filter containers created by Kubernetes. If empty, it returns all containers 
        except from 'kube-system' namespace
        to_tuple (bool): Return a list of namedtuples that represent a pair of container and container name 
    """
    containers = client.containers.list()
    _filter = lambda x: 'POD' not in x.name and namespace in x.name and 'kube-system' not in x.name

    if not to_tuple:
        return list(filter(_filter, containers))
    return list(map(lambda container: Pair(container, container.name), filter(_filter, containers)))
