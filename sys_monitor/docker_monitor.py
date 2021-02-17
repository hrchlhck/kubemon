from addict import Dict
from .utils import subtract_dicts, format_name, get_containers, get_container_pid, send
from .constants import CONNECTION_DIED_CODE
from .process_monitor import parse_proc_net, ProcessMonitor
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
from threading import Thread
import psutil
import docker
import time
import os
import sys


class DockerMonitor(ProcessMonitor):
    def __init__(self, address, port, interval=5):
        self.__address = address
        self.__port = port
        self.__interval = interval

    def collect(self, container_name: str, pid: int) -> None:
        """ 
        Method to collects all data from all container processes

        Args:
            container_name (str): Container name
            pid (int): Pid of the container process

        """
        process = psutil.Process(pid=pid)
        send(self.__address, self.__port, self.get_pchild_usage,
             self.__interval, "docker_monitor", container_name, process.pid)

    def start(self):
        client = docker.from_env()
        containers = get_containers(client)
        container_pids = [(c.name, get_container_pid(c)) for c in containers]
        for name, pid in container_pids:
            t = Thread(target=self.collect, args=(name, pid))
            t.start()
