from subprocess import check_output
from functools import reduce
from os.path import join, isfile
from pathlib import Path
from typing import List
from requests import get
from .config import DATA_PATH
from .decorators import wrap_exceptions
from .dataclasses import Pair
from time import sleep

import docker
import socket
import csv
import pickle
import struct
import json

__all__ = ['subtract_dicts', 'merge_dict', 'filter_dict', 'join_url', 'send_data',
           'save_csv', 'format_name', 'get_containers', 'get_container_pid', 'try_connect', 'receive', 'send_to']


def subtract_dicts(dict1: dict, dict2: dict, operation=lambda x, y: x-y) -> dict:
    """ Subtracts values from dict1 and dict2 """
    if len(dict1) != len(dict2):
        raise KeyError("Mapping key not found")
    values = map(lambda _dict: reduce(operation, _dict),
                 zip(dict2.values(), dict1.values()))
    return dict(zip(dict1.keys(), map(lambda n: round(n, 4), values)))


def merge_dict(*dicts: List[dict]) -> dict:
    """ Merges multiple dictionaries """
    assert dicts != None
    assert all(i for i in dicts if isinstance(i, dict)) == True
    ret = dict()
    for d in dicts:
        ret.update(d)
    return ret


def filter_dict(_dict: dict, *keys: List[object]) -> dict:
    """ Apply a simple filter over a given dictionary
        Usage:
            >>> filter_dict({'a': 1, 'b': 2, 'c':3}, 'a', 'c')
            >>> {'a': 1, 'c': 3}
    """
    filters = keys
    if isinstance(keys[0], list):
        filters = keys[0]
    return {k: v for k, v in _dict.items() if k in filters}


def join_url(url: str, *pages: List[str]) -> str:
    """ Joins pages in a given URL. 
        Usage:
            >>> join('https://github.com', 'hrchlhck', 'sys-monitor')
            >>> 'https://github.com/hrchlhck/sys-monitor'
    """
    for page in map(str, pages):
        url += "/" + page
    return url


def load_json(url: str) -> dict:
    """ Parses a JSON to a Python dictionary """
    try:
        return get(url).json()
    except Exception as e:
        print(e)


def send_data(socket: socket.socket, data: dict, source: str) -> None:
    """ 
    This function is responsible for sending data via network socket
    to a TCP Server inside of sys_monitor/collector.py.

    Args:
        data (dict): A dictionary containing your data
        source (str) From where you are sending the data
        socket (socket.socket) TCP socket
    """
    temp = pickle.dumps({"source": source, "data": data})
    socket.send(temp)


def save_csv(_dict: dict, name: str, dir_name="", output_dir=DATA_PATH) -> None:
    """ 
    Saves a dict into a csv 

    Args:
        _dict (dict): The dictionary that will be written or appended in the file
        name (str): The name of the file
        dir_name (str): Subdirectory inside .config.DATA_PATH that the file will be saved

    Raises:
        ValueError 
            if `dir_name` type isn't string 
    """
    filename = "%s.csv" % name

    if dir_name and not isinstance(dir_name, str):
        raise ValueError("Expected str instead of %s" % type(dir_name))
    elif dir_name and isinstance(dir_name, str):
        output_dir = output_dir.joinpath(dir_name)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_dir = join(output_dir, filename)

    mode = "a"

    if not isfile(output_dir):
        mode = "w"

    with open(output_dir, mode=mode, newline="") as f:
        writer = csv.DictWriter(f, _dict.keys())

        if mode == "w":
            writer.writeheader()

        writer.writerow(_dict)


def format_name(name):
    return "%s" % name.split('-')[0]


def get_containers(client: docker.client.DockerClient, namespace='', to_tuple=False) -> List[docker.client.ContainerCollection]:
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


def get_container_pid(container):
    get_pid = lambda x: x['State']['Pid']

    with open(f'/var/lib/docker/containers/{container.id}/config.v2.json', 'r') as fp:
        data = fp.read()
        data = json.loads(data)
        return get_pid(data)


def try_connect(addr: str, port: int, _socket: socket.socket, timeout: int) -> None:
    """ 
        Function to try connection of a socket to a server

        Args:
            addr (str): Address of the server
            port (int): It's port
            _socket (socket.socket): Socket object you want to connect to the server
            timeout (int): Connection attempts
    """
    for i in range(timeout):
        print("Attempt %d" % int(i + 1))
        try:
            return _socket.connect((addr, port))
        except Exception as e:
            print(e)
        sleep(1)
    print("Connection timed out after %s retries" % str(timeout))
    exit(0)


def receive(_socket: socket.socket, encoding_type='utf8') -> str:
    """ 
    Wrapper function for receiving data from a socket. It also decodes it to utf8 by default.

    Args:
        _socket (socket): Socket that will be receiving data from;
        encoding_type (str): Encoding type for decoding incoming data.
    """
    # UDP
    addr = None
    if _socket.type == 2:
        recv_size, _ = _socket.recvfrom(4)
        buffer_size = struct.unpack('I', recv_size)[0]
        data, addr = _socket.recvfrom(buffer_size)
    else:
        recv_size = _socket.recv(4)
        buffer_size = struct.unpack('I', recv_size)[0]
        data = _socket.recv(buffer_size)

    data = pickle.loads(data, encoding=encoding_type)
    return data, addr


@wrap_exceptions(KeyboardInterrupt)
def send_to(_socket: socket.socket, data: object, address=tuple()) -> None:
    byte_data = pickle.dumps(data)
    size = struct.pack('I', len(byte_data))

    # UDP
    if _socket.type == 2 and address:
        _socket.sendto(size, address)
        _socket.sendto(byte_data, address)
    else:
        _socket.send(size)
        _socket.send(byte_data)

def get_default_nic():
    """ Function to get the default network interface in a Linux-based system. """
    # Source: https://stackoverflow.com/a/20925510/12238188

    route = '/proc/net/route'
    with open(route, mode='r') as fd:
        # Removing spaces and separating fields
        lines = list(map(lambda x: x.strip().split(), fd))
        
        # Removing header
        lines.pop(0)

        # Parsing nic
        for iface in lines:
            name = iface[0]
            dest = iface[1]
            flags = iface[3]

            if dest != '00000000' or not int(flags, 16) & 2:
                continue
            return name

def get_host_ip():
    """ Returns the actual IPaddress from the host """
    # Source:https://stackoverflow.com/a/30990617/12238188 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
        sockfd.connect(('8.8.8.8', 80))
        return sockfd.getsockname()[0]

def is_alive(address: str, port: int) -> bool:
    sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sockfd.connect((address, port))
        return True
    except:
        sockfd.close()
        return False
