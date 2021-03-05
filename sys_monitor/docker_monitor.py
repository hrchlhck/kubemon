from .utils import subtract_dicts, filter_dict
from .base_monitor import BaseMonitor
from .utils import get_container_pid
from .process_monitor import parse_proc_net, ProcessMonitor
from .entities.disk import Disk
from .pod import *
from threading import Thread
from time import sleep
from typing import List
import docker
import psutil
import time
import os
import sys

__all__ = ['DockerMonitor']

class DockerMonitor(BaseMonitor):
    def __init__(self, kubernetes=True, namespace='k8s-bigdata', stats_path="/sys/fs/cgroup", *args, **kwargs):
        super(DockerMonitor, self).__init__(*args, **kwargs)
        self.__stats_path = stats_path
        if kubernetes:
            self.__pods = Pod.list_containers_cgroups('systemd', namespace=namespace, client=docker.from_env())

    @property
    def pods(self):
        return self.__pods

    @property
    def stats_path(self):
        return self.__stats_path

    def get_path(self, cgroup_controller: str, stat: str, container: Pair=None, pod: Pod=None) -> str:
        """ 
        Get full path of the docker container within the pod, on cgroups directory 
        
        Args:
            pod (Pod): Pod object
            container (Pair): Named tuple object to represent a container
            cgroup_controller (str): cgroup controller. E.g. cpuacct, memory, blkio, etc.
            stat (str): file inside cgroup_controller
            _alt_path (str): Alternative path to be gathering data
        """
        if pod and not container:
            ret = f"{self.stats_path}/{cgroup_controller}/kubepods.slice/kubepods-besteffort.slice/kubepods-besteffort-pod{pod.id}.slice/docker-{container.id}.scope/{cgroup_controller}.{stat}"
        elif container and not pod: 
            ret = f"{self.stats_path}/{cgroup_controller}/system.slice/docker-{container.id}.scope/{cgroup_controller}.{stat}"
        else:
            ret = f"{self.stats_path}/{cgroup_controller}.{stat}"
        
        return ret

    @staticmethod
    def parse_fields(data: List[List[str]]) -> dict:
        """
            Parse fields on cgroups files or any file that contains the following pattern:

            input -> [[str int],
                      [str int],
                      [str int],
                      ...]
            output -> {str: int, str: int, str: int, ...}
            
            Args:
                data (list): List of lists representing a pair of data
        """
        to_int = lambda x: int(x) if x.isdigit() else x
        data = list(map(lambda x: x.replace('\n', '').split(), data))
        field_count = list(filter(lambda x: len(x) > 2, data))

        # Checking columns to avoid dict exceptions
        if len(field_count) >= 1:
            ret = list(map(lambda x: tuple(map(lambda y: to_int(y), x)), data))
        else:
            ret = {k: to_int(v) for k, v in data}

        return ret

    def get_memory_usage(self, container: Pair=None, pod: Pod=None) -> dict:
        """ 
        Get the memory usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
            _alt_path (str): Alternative path to be gathering data
        """
        fields = ['rss', 'cache', 'mapped_file', 'pgpgin', 'pgpgout', 'pgfault', 'pgmajfault', 'active_anon', 'inactive_anon', 'active_file', 'inactive_file', 'unevictable']
        path = self.get_path(container=container, pod=pod, cgroup_controller='memory', stat='stat')

        with open(path, mode='r') as fd:
            data = DockerMonitor.parse_fields(list(fd))
        
        ret = filter_dict(data, fields)
        return ret

    def get_disk_usage(self, container: Pair=None, pod: Pod=None, **kwargs) -> dict:
        """ 
        Get the disk usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
            disk_name (str): Name of the disk to collect major and minor device drivers (only for parsing purposes)
            _alt_path (str): Alternative path to be gathering data
        """
        path = self.get_path(container=container, pod=pod, cgroup_controller='blkio', stat='throttle.io_service_bytes')
        disk = Disk(**kwargs)
        dev = f"{disk.major}:{disk.minor}"

        with open(path, mode='r') as fd:
            data = DockerMonitor.parse_fields(list(fd))

        # Filter blkio stats by disk maj:min
        data = filter(lambda x: len(x) == 3, data)
        data = filter(lambda x: x[0] == dev, data)
        data = map(lambda x: x[1:], data)

        # Map to dict
        ret = {k: v for k, v in data}

        return ret

    def get_cpu_times(self, container: Pair=None, pod: Pod=None) -> dict:
        """ 
        Get the CPU usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
            _alt_path (str): Alternative path to be gathering data
        """
        path = self.get_path(container=container, pod=pod, cgroup_controller='cpuacct', stat='stat')
        ret = dict()

        with open(path, mode='r') as fd:
            data = DockerMonitor.parse_fields(list(fd))

        return data

    def get_net_usage(self, container: Pair) -> dict:
        """ 
        Get network usage of a given container within a pod 

        To understand why not gather information from cgroups, please refer to https://docs.docker.com/config/containers/runmetrics/#network-metrics
        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
            _alt_path (str): Alternative path to be gathering data
        """

        return ProcessMonitor.get_net_usage(get_container_pid(container.container))

    def get_stats(self, container: Pair, pod: Pod=None) -> dict:
        """ 
        Get all metrics of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        cpu = self.get_cpu_times(container, pod)
        memory = self.get_memory_usage(container, pod)
        network = self.get_net_usage(container)
        disk = self.get_disk_usage(container, pod, disk_name='sdb')

        sleep(self.interval)

        cpu_new = subtract_dicts(cpu, self.get_cpu_times(container, pod))
        memory_new = subtract_dicts(memory, self.get_memory_usage(container, pod))
        network_new = subtract_dicts(network, self.get_net_usage(container))
        disk_new = subtract_dicts(disk, self.get_disk_usage(container, pod, disk_name='sdb'))

        ret = {**cpu_new, **memory_new, **network_new, **disk_new}
        return ret

    def collect(self, container: Pair, pod: Pod=None) -> None:
        """ 
        Method to collects all data from all container processes

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        func_args = (container, pod)
        super(DockerMonitor, self).send(function=self.get_stats, function_args=func_args, _from=self.name, container_name=container.name)

    def start(self) -> None:
        super(DockerMonitor, self).start()
