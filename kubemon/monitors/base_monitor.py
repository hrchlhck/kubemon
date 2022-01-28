from ..utils import (
    get_host_ip, receive, 
    send_to, filter_dict
)

from ..config import (
    DEFAULT_MONITOR_PORT, START_MESSAGE, 
    DEFAULT_MONITOR_INTERVAL
)

from ..decorators import wrap_exceptions
from typing import Callable
from ..log import create_logger
from enum import Enum

import socket
import os
import sys

LOGGER = create_logger(__name__)

class MonitorFlag(Enum):
    IDLE = 0
    RUNNING = 1
    NOT_CONNECTED = 2
    STOPPED = 3

class BaseMonitor:
    def __init__(self, address, port=DEFAULT_MONITOR_PORT, interval=DEFAULT_MONITOR_INTERVAL):
        self.__address = address
        self.__port = port
        self.__interval = interval
        self.__flag = MonitorFlag.NOT_CONNECTED
        self.__stop_request = False

    @property
    def address(self):
        return self.__address

    @property
    def port(self):
        return self.__port

    @property
    def interval(self):
        return self.__interval

    @property
    def name(self):
        return self.__class__.__name__
    
    @property
    def flag(self) -> MonitorFlag:
        return self.__flag
    
    @flag.setter
    def flag(self, val: MonitorFlag) -> None:
        if isinstance(val, MonitorFlag):
            self.__flag = val
        else:
            raise ValueError('The value must be a MonitorFlag instance')
    
    @property
    def stop_request(self) -> bool:
        return self.__stop_request
    
    @stop_request.setter
    def stop_request(self, val: bool) -> None:
        if isinstance(val, bool):
            self.__stop_request = val
        else:
            raise ValueError('The value must be a boolean')

    def __str__(self) -> str:
        return f'<{self.name} - {socket.gethostname()} - {get_host_ip()}>'
    
    def __repr__(self) -> str:
        return f'<{self.name} - {socket.gethostname()} - {get_host_ip()}>'

    @staticmethod
    def get_memory_usage(pid=None):
        """ 
        Returns the memory usage based on /proc virtual file system available in the Linux kernel. 
        Any questions, please refer to https://man7.org/linux/man-pages/man5/proc.5.html

        Args:
            pid (int): If not None, get system-wide information about memory usage, otherwise
                       it will return based on a given pid.
        """
        if pid and str(pid) not in os.listdir('/proc'):
            LOGGER.debug(f"No pid {pid}")

        if not pid:
            fields = ['nr_active_file', 'nr_inactive_file', 'nr_mapped', 'nr_active_anon', 'nr_inactive_anon', 'pgpgin', 'pgpgout', 'pgfree', 'pgfault', 'pgmajfault', 'pgreuse']
            
            def to_dict(nested_lists):
                atoms = map(lambda atom_list: atom_list.split(), nested_lists)
                ret = {k: int(v) for k, v in atoms}
                LOGGER.debug(f"Memory: {ret}")
                return ret

            with open("/proc/vmstat", mode="r") as fd:
                ret = to_dict(fd.readlines())
                ret = filter_dict(ret, fields)
            LOGGER.debug(f"Filtered data: {ret}")
        else:
            with open('/proc/%s/statm' % pid, mode='r') as fd:
                infos = ['size', 'resident', 'shared',
                         'text', 'lib', 'data', 'dt']
                ret = fd.read()
                ret = {k: int(v) for k, v in zip(infos, ret.split())}
                LOGGER.debug(f"Ret with pid {pid}: {ret}")
        return ret

    def get_source_name(self, pid=0, container_name=""):
        """ 
            Returns a standardized name to be sended to the collector instance

            Standard: 
                if monitor instance is OSMonitor, then
                    (Monitor instance)_(IP address)_(Hostname)_(PID = 0)
                else
                    (Monitor instance)_(IP address)_(Hostname)_(Container name)_(PID)

            Args:
                pid (int): Represents the PID of a process or docker container
                container_name (str): Represents the name of the process or docker container
        """
        parse_ip = lambda ip: ip.replace(".", "_")
        ip = parse_ip(get_host_ip())
        ret = f"{self.name}_{ip}_{socket.gethostname()}_{pid}"

        if self.name == "ProcessMonitor" or self.name == "DockerMonitor":
            ret = f"{self.name}_{ip}_{socket.gethostname()}_{container_name}_{pid}"
        
        LOGGER.debug(f"Got name {ret}")

        return ret

    def send(self, function: Callable, function_args: list, container_name="", pid=0) -> None:
        """ 
        Wrapper function for gathering and sending data from docker containers in a gap of N seconds defined by `interval` parameter.

        Args:
            function (Callable): The function that will be gathering information
            function_args (list): The arguments of the `function` parameter
            container_name (str): Name of the container
            pid (int): If it's not None, it will specify a PID for monitoring and gathering data
        """

        source_name = self.get_source_name(pid=pid, container_name=container_name)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
            sockfd.connect((self.address, self.port))

            LOGGER.info(f"[ {source_name} ] Connected collector to server")

            send_to(sockfd, source_name)
            LOGGER.debug(f"Sent my name to collector at {self.address}:{self.port}")

            while True:
                try:
                    signal, _ = receive(sockfd)
                    LOGGER.debug(f"Received signal {START_MESSAGE}")
                except EOFError:
                    LOGGER.error("Monitor died")
                    exit()

                self.flag = MonitorFlag.IDLE
                if signal == START_MESSAGE:
                    LOGGER.info(f"[ {source_name} ] Starting")

                    self.flag = MonitorFlag.RUNNING
                    
                    while not self.stop_request:
                        ret = function(*function_args)

                        message = {"source": source_name, "data": ret}

                        try:
                            send_to(sockfd, message)
                            LOGGER.debug(f"Sent {sys.getsizeof(message)} bytes to {self.address}:{self.port}")

                            recv, _ = receive(sockfd)
                            
                            LOGGER.debug(f"Received {sys.getsizeof(recv)} from {self.address}:{self.port}")
                        except EOFError:
                            LOGGER.error(f"[ {source_name} ] Monitor died")
                            exit()
                    
                    if self.stop_request:
                        LOGGER.info(f'Stopped monitor {source_name}')
                        self.stop_request = False
                        self.flag = MonitorFlag.STOPPED