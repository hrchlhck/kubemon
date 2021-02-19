from .utils import subtract_dicts
from .process_monitor import ProcessMonitor
from .process_monitor import parse_proc_net
from threading import Thread
import psutil
import time
import os
import sys


class DockerMonitor(ProcessMonitor):
    def __init__(self, *args, **kwargs):
        super(DockerMonitor, self).__init__(*args, **kwargs)

    def collect(self, container_name: str, pid: int) -> None:
        """ 
        Method to collects all data from all container processes

        Args:
            container_name (str): Container name
            pid (int): Pid of the container process

        """
        process = psutil.Process(pid=pid)
        super(DockerMonitor, self).send(self.address, self.port, super().get_pchild_usage,
                                        self.interval, self.name, container_name, process.pid)

    def start(self):
        super(DockerMonitor, self).start()
