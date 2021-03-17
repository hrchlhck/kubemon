import docker
from .utils import get_containers, get_container_pid, format_name, try_connect, receive, send_to, filter_dict
from .exceptions import PidNotExistException
from .decorators import wrap_exceptions
from .constants import START_MESSAGE
from typing import Callable
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
from threading import Thread
import os


class BaseMonitor(object):
    def __init__(self, address, port, interval=5):
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
            raise PidNotExistException("Pid %s does not exist" % pid)

        if not pid:
            fields = ['nr_active_file', 'nr_inactive_file', 'nr_mapped', 'nr_active_anon', 'nr_inactive_anon', 'pgpgin', 'pgpgout', 'pgfree', 'pgfault', 'pgmajfault', 'pgreuse']
            
            def to_dict(nested_lists): return {k: int(v) for k, v in map(
                lambda atom_list: atom_list.split(), nested_lists)}

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

    @wrap_exceptions(KeyboardInterrupt, EOFError)
    def send(self, function: Callable, function_args: list, _from="", container_name="", pid=0) -> None:
        """ 
        Wrapper function for gathering and sending data from docker containers in a gap of N seconds defined by `interval` parameter.

        Args:
            function (Callable): The function that will be gathering information
            function_args (list): The arguments of the `function` parameter
            _from (str): Name where the data is being sent
            container_name (str): Name of the container
            pid (int): If it's not None, it will specify a PID for monitoring and gathering data
        """
        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            try_connect(self.address, self.port, sock, self.interval)

            print("Connected %s collector to server" % format_name(_from))

            signal = receive(sock)

            if signal == START_MESSAGE:
                print("Starting")

                while True:
                    ret = function(*function_args)

                    print(ret)

                    source = f"{_from}_{format_name(container_name)}_{pid}"

                    print(source)

                    message = {"source": str(source), "data": dict(ret)}

                    send_to(sock, message, to_group=False)

                    print(receive(sock))

    def collect(self):
        """ Method to be implemented by child classes """

    def start(self):
        class_name = self.name

        if "OSMonitor" == class_name:
            self.send(self.collect, [self.interval], _from=class_name)
        elif "ProcessMonitor" == class_name:
            client = docker.from_env()
            containers = get_containers(client)
            container_pids = [(c.name, get_container_pid(c))
                              for c in containers]
            for container_name, pid in container_pids:
                t = Thread(target=self.collect, args=(container_name, pid))
                t.start()
        elif "DockerMonitor" == class_name:
            pods = self.pods
            for pod, containers in pods.items():
                for container in containers:
                    t = Thread(target=self.collect, kwargs={
                               'container': container, 'pod': pod})
                    t.start()
