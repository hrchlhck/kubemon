import docker
from .utils import get_containers, get_container_pid, format_name, try_connect, receive, send_to
from .decorators import wrap_exceptions
from .constants import START_MESSAGE
from typing import Callable
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
from threading import Thread

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

    @wrap_exceptions(KeyboardInterrupt, EOFError)
    def send(self, address: str, port: int, function: Callable, interval: int, _from="", container_name="", pid=0) -> None:
        """ 
        Wrapper function for gathering and sending data from docker containers in a gap of N seconds defined by `interval` parameter.

        Args:
            address (str): Address of the server that this function will be sending the data
            port (int): The port
            function (Callable): The function that will be gathering information
            interval (int): The time in seconds that the function will be "sleeping"
            _from (str): Name where the data is being sent
            container_name (str): Name of the container
            pid (int): If it's not None, it will specify a PID for monitoring and gathering data

        """
        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            try_connect(address, port, sock, interval)

            print("Connected %s collector to server" % format_name(_from))

            signal = receive(sock)

            if signal == START_MESSAGE:
                print("Starting")

                while True:
                    if pid:
                        ret = function(interval, pid)
                    else:
                        ret = function(interval)

                    print(ret)

                    source = "%s_%s_%s" % (_from, format_name(container_name), pid)
                    message = {"source": source, "data": ret}
                    
                    send_to(sock, message)

                    print(receive(sock))

    def collect(self):
        """ Method to be implemented by child classes """

    def start(self):
        class_name = self.name

        if "OSMonitor" == class_name:
            self.send(self.address, self.port, self.collect, self.interval, class_name)
        elif "ProcessMonitor" == class_name or "DockerMonitor" == class_name:
            client = docker.from_env()
            containers = get_containers(client)
            container_pids = [(c.name, get_container_pid(c)) for c in containers]

            for container_name, pid in container_pids:
                t = Thread(target=self.collect, args=(container_name, pid))
                t.start()