from dataclasses import dataclass

from docker.models.containers import Container

__all__ = ['Pair', 'Pod']

@dataclass
class Pair:
    """ Dataclass to represent a container Pair """
    container: Container
    name: str

@dataclass(frozen=True)
class Pod:
    """ Dataclass to represent a pod from kubernetes """
    namespace: str
    name: str
    container_name: str
    pod_id: str
    container_id: str
    container: Container
