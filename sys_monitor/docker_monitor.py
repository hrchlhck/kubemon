from .utils import subtract_dicts, filter_dict
from .base_monitor import BaseMonitor
from .utils import get_container_pid
from .process_monitor import parse_proc_net, ProcessMonitor
from .pod import *
from threading import Thread
from time import sleep
from typing import List
import docker
import psutil
import time
import os
import sys
    

class DockerMonitor(BaseMonitor):
    def __init__(self, namespace='k8s-bigdata', *args, **kwargs):
        super(DockerMonitor, self).__init__(*args, **kwargs)
        self.__pods = Pod.list_containers_cgroups('systemd', namespace=namespace, client=docker.from_env())

    @property
    def pods(self):
        return self.__pods

    @staticmethod
    def get_path(pod: Pod, container: Pair, cgroup_controller: str, stat: str) -> str:
        """ 
        Get full path of the docker container within the pod, on cgroups directory 
        
        Args:
            pod (Pod): Pod object
            container (Pair): Named tuple object to represent a container
            cgroup_controller (str): cgroup controller. E.g. cpuacct, memory, blkio, etc.
            stat (str): file inside cgroup_controller
        """
        return "/sys/fs/cgroup/%s/kubepods.slice/kubepods-besteffort.slice/kubepods-besteffort-pod%s.slice/docker-%s.scope/%s.%s" % (cgroup_controller, pod.id, container.id, cgroup_controller, stat)

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
        data = [d.split() for d in data]
        ret = {k: to_int(v) for k, v in data}
        return ret

    def get_memory_usage(self, pod: Pod, container: Pair) -> dict:
        """ 
        Get the memory usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        fields = ['rss', 'cache', 'mapped_file', 'pgpgin', 'pgpgout', 'pgfault', 'pgmajfault', 'active_anon', 'inactive_anon', 'active_file', 'inactive_file', 'unevictable']
        path = DockerMonitor.get_path(pod, container, 'memory', 'stat')

        with open(path, mode='r') as fd:
            data = fd.readlines()
        
        ret = DockerMonitor.parse_fields(data)
        ret = filter_dict(ret, fields)
        return ret

    def get_disk_usage(self, pod: Pod, container: Pair) -> dict:
        """ 
        Get the disk usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        return {    }

    def get_cpu_times(self, pod: Pod, container: Pair) -> dict:
        """ 
        Get the CPU usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        cgroup_stats = ['stat', 'usage_user', 'usage_sys']
        ret = dict()
        for stat in cgroup_stats:
            path = DockerMonitor.get_path(pod, container, 'cpuacct', stat)
        
            with open(path, mode='r') as fd:
                data = fd.readlines()
            
            if stat == 'stat':
                ret.update(DockerMonitor.parse_fields(data))
            else:
                ret.update({stat: int(data[0])})
        return ret

    def get_net_usage(self, container: Pair) -> dict:
        """ 
        Get network usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """

        return ProcessMonitor.get_net_usage(get_container_pid(container.container))

    def get_stats(self, pod: Pod, container: Pair) -> dict:
        """ 
        Get all metrics of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        cpu = self.get_cpu_times(pod, container)
        memory = self.get_memory_usage(pod, container)
        network = self.get_net_usage(container)
        disk = self.get_disk_usage(pod, container)

        sleep(self.interval)

        cpu_new = subtract_dicts(cpu, self.get_cpu_times(pod, container))
        memory_new = subtract_dicts(memory, self.get_memory_usage(pod, container))
        network_new = subtract_dicts(network, self.get_net_usage(container))
        disk_new = subtract_dicts(disk, self.get_disk_usage(pod, container))

        ret = {**cpu_new, **memory_new, **network_new, **disk_new}
        return ret

    def collect(self, pod: Pod, container: Pair) -> None:
        """ 
        Method to collects all data from all container processes

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        func_args = (pod, container)
        super(DockerMonitor, self).send(function=self.get_stats, function_args=func_args, _from=self.name, container_name=container.name)

    def start(self) -> None:
        super(DockerMonitor, self).start()
