from ..utils import get_containers, get_container_pid, receive, send_to, filter_dict
from ..decorators import wrap_exceptions
from ..config import START_MESSAGE, DEFAULT_MONITOR_INTERVAL
from typing import Callable
from threading import Thread
import socket
import docker
import os


class BaseMonitor(object):
    def __init__(self, address, port, interval=DEFAULT_MONITOR_INTERVAL):
        self.__address = address
        self.__port = port
        self.__interval = interval

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
            print(f"No pid {pid}")

        if not pid:
            fields = ['nr_active_file', 'nr_inactive_file', 'nr_mapped', 'nr_active_anon', 'nr_inactive_anon', 'pgpgin', 'pgpgout', 'pgfree', 'pgfault', 'pgmajfault', 'pgreuse']
            
            def to_dict(nested_lists):
                atoms = map(lambda atom_list: atom_list.split(), nested_lists)
                ret = {k: int(v) for k, v in atoms}
                return ret

            with open("/proc/vmstat", mode="r") as fd:
                ret = to_dict(fd.readlines())
                ret = filter_dict(ret, fields)
        else:
            with open('/proc/%s/statm' % pid, mode='r') as fd:
                infos = ['size', 'resident', 'shared',
                         'text', 'lib', 'data', 'dt']
                ret = fd.read()
                ret = {k: int(v) for k, v in zip(infos, ret.split())}
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
        ip = parse_ip(socket.gethostbyname(socket.gethostname()))
        ret = f"{self.name}_{ip}_{socket.gethostname()}_{pid}"

        if self.name == "ProcessMonitor" or self.name == "DockerMonitor":
            ret = f"{self.name}_{ip}_{socket.gethostname()}_{container_name}_{pid}"

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

            print(f"[ {source_name} ] Connected collector to server", flush=True)

            send_to(sockfd, source_name)

            try:
                signal, _ = receive(sockfd)
            except EOFError:
                print("Monitor died")
                exit()

            if signal == START_MESSAGE:
                print(f"[ {source_name} ] Starting", flush=True)

                while True:
                    ret = function(*function_args)

                    message = {"source": source_name, "data": ret}

                    try:
                        send_to(sockfd, message)

                        recv, _ = receive(sockfd)
                    except EOFError:
                        print(f"[ {source_name} ] Monitor died")
                        exit()

    def collect(self):
        """ Method to be implemented by child classes """

    def start(self):
        class_name = self.name
        
        if "OSMonitor" == class_name:
            self.send(function=self.collect, function_args=[])
        elif "ProcessMonitor" == class_name:
            client = docker.from_env()
            containers = get_containers(client)
            container_pids = [(c.name, get_container_pid(c)) for c in containers]
            for container_name, pid in container_pids:
                t = Thread(target=self.collect, args=(container_name, pid))
                t.start()
        elif "DockerMonitor" == class_name:
            for pod in self.pods:
                for c in pod.containers:
                    t = Thread(target=self.collect, kwargs={
                               'container': c, 'pod': pod})
                    t.start()
