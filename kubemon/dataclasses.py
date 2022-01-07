import dataclasses
import socket
from docker.models.containers import Container

__all__ = ['Pair', 'Client']

@dataclasses.dataclass
class Client:
    """ Dataclass to represent a socket object returned by socket.accept() """
    name: str
    socket_obj: socket.socket
    address: tuple

@dataclasses.dataclass
class Pair:
    """ Dataclass to represent a container Pair """
    container: Container
    name: str