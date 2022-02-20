from docker.models.containers import Container
from typing import List
from collections import namedtuple

from kubemon.log import create_logger
from kubemon.dataclasses import Pod

import docker

__all__ = ['Pair', 'Pod']

Pair = namedtuple('Pair', ['name', 'id'])

LOGGER = create_logger(__name__)

def to_pod(container: Container) -> Pod:
    c_name = container.name
    fields = c_name.split('_')

    return Pod(fields[3], fields[2], fields[1], fields[4], container.id, container)

def list_pods(*namespaces, client=None, except_namespace='kube-system', from_k8s=True) -> List[Pod]:
    if client == None:
        client = docker.from_env()
    elif not isinstance(client, docker.client.DockerClient):
        raise TypeError(f'Must specify the DockerClient object instead of \'{type(client).__name__}\'')

    containers = client.containers.list()

    if not from_k8s:
        return containers

    if not any(c for c in containers if 'k8s' in c.name) or not len(namespaces):
        return list()

    containers = [c for c in containers if 'POD' not in c.name]

    # Get pods from a list of namespaces.
    # Otherwise, it returns all pods from all namespaces
    if not namespaces[0] == '*':
        containers = [c 
            for c in containers 
            for namespace in namespaces 
            if namespace in c.name \
            and except_namespace not in c.name
        ]

    return list(map(to_pod, containers))
