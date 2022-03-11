from kubemon.settings import Volatile

from pathlib import Path
from typing import List, Tuple
from requests import get as rget

import socket
import pickle
import fcntl
import struct
import psutil

Volatile.set_procfs(psutil.__name__)

__all__ = ['receive', 'send_to', 'get_default_nic', 'get_host_ip', 'is_alive', 'gethostname', 'get_json']

def receive(_socket: socket.socket, encoding_type='utf8', buffer_size=1024) -> str:
    """ 
    Wrapper function for receiving data from a socket. It also decodes it to utf8 by default.

    Args:
        _socket (socket): Socket that will be receiving data from;
        encoding_type (str): Encoding type for decoding incoming data.
    """
    # UDP
    addr = None
    if _socket.type == 2:
        # recv_size, _ = _socket.recvfrom(4)
        # buffer_size = struct.unpack('I', recv_size)[0]
        data, addr = _socket.recvfrom(buffer_size)
    else:
        # recv_size = _socket.recv(4)
        # buffer_size = struct.unpack('I', recv_size)[0]
        data = _socket.recv(buffer_size)

    data = pickle.loads(data, encoding=encoding_type)
    return data, addr

def send_to(_socket: socket.socket, data: object, address=tuple()) -> None:
    byte_data = pickle.dumps(data)
    # size = struct.pack('I', len(byte_data))

    # UDP
    if _socket.type == 2 and address:
        # _socket.sendto(size, address)
        _socket.sendto(byte_data, address)
    else:
        # _socket.send(size)
        _socket.send(byte_data)

def get_default_nic():
    """ Function to get the default network interface in a Linux-based system. """
    # Source: https://stackoverflow.com/a/20925510/12238188

    route = f'{psutil.PROCFS_PATH}/net/route'
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

def get_host_ip(ifname: str = "") -> str:
    """ Returns the actual IP address from the host """
    # Source: https://stackoverflow.com/a/24196955
    if not ifname:
        ifname = get_default_nic()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname.encode())
    )[20:24])

def is_alive(address: str, port: int) -> bool:
    sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sockfd.connect((address, port))
        ret = True
    except:
        ret = False
    
    sockfd.close()

    return ret

def gethostname() -> str:
    if Path('/etc/host_hostname').exists():
        with open('/etc/host_hostname', mode='r') as fp:
            return fp.read().strip()
    return socket.gethostname()

def nslookup(addr: str, port: int) -> List[str]:
    try:
        sockets = socket.getaddrinfo(addr, port)
        return [s[-1][0] for s in sockets if s[1] == socket.SOCK_STREAM]
    except socket.gaierror:
        return []

def get_json(url: str) -> Tuple[dict, int]:
    req = rget(url, timeout=30)

    if req.status_code == 200:
        return req.json(), req.status_code
    return dict(), req.status_code
