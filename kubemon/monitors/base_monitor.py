from ..utils import get_containers, get_container_pid, get_host_ip, receive, send_to, filter_dict
from ..decorators import wrap_exceptions
from ..config import START_MESSAGE, DEFAULT_MONITOR_INTERVAL
from typing import Callable
from threading import Thread, Lock
from ..log import create_logger
import socket
import docker
import os
import sys

LOGGER = create_logger(__name__)

class BaseMonitor:
    def __init__(self, address, port, interval=DEFAULT_MONITOR_INTERVAL):
        self.__address = address
        self.__port = port
        self.__interval = interval
        self.mutex = Lock()

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

    @wrap_exceptions(KeyboardInterrupt)
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

            try:
                signal, _ = receive(sockfd)
                LOGGER.debug(f"Received signal {START_MESSAGE}")
            except EOFError:
                LOGGER.error("Monitor died")
                exit()

            if signal == START_MESSAGE:
                LOGGER.info(f"[ {source_name} ] Starting")

                while True:
                    ret = function(*function_args)

                    message = {"source": source_name, "data": ret}

                    try:
                        send_to(sockfd, message)
                        LOGGER.debug(f"Sent {sys.getsizeof(message)} bytes to {self.address}:{self.port}")

                        recv, _ = receive(sockfd)
                        
                        LOGGER.debug(f"Received {recv} from {self.address}:{self.port}")
                    except EOFError:
                        LOGGER.error(f"[ {source_name} ] Monitor died")
                        exit()

    def collect(self):
        """ Method to be implemented by child classes """

    def start(self):
        class_name = self.name
        
        if "OSMonitor" == class_name:
            LOGGER.debug("Starting OSMonitor")
            self.send(function=self.collect, function_args=[])
        elif "ProcessMonitor" == class_name:
            client = docker.from_env()
            containers = get_containers(client)
            container_pids = [(c.name, get_container_pid(c)) for c in containers]

            for container_name, pid in container_pids:
                t = Thread(target=self.collect, args=(container_name, pid))
                t.start()
                LOGGER.debug(f"Starting ProcessMonitor for container '{container_name}' with pid '{pid}'")

        elif "DockerMonitor" == class_name:
            for pod in self.pods:
                for c in pod.containers:
                    t = Thread(target=self.collect, kwargs={
                               'container': c, 'pod': pod})
                    t.start()
                    LOGGER.debug(f"Starting DockerMonitor for container '{c}' in pod '{pod}'")
