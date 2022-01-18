from threading import Thread

from docker.models.containers import Container
from kubemon.config import DEFAULT_DISK_PARTITION
from ..utils import subtract_dicts, filter_dict, get_container_pid
from .base_monitor import BaseMonitor
from .process_monitor import ProcessMonitor
from ..log import create_logger
from ..entities.disk import Disk
from ..pod import *
from time import sleep
from typing import List

__all__ = ['DockerMonitor']

LOGGER = create_logger(__name__)

class StatParser:
    ''' Class to parse docker metrics to fit into a CSV format, by saving into a flat dictionary. '''

    def _parse_blkio_operations(data: List[dict]) -> dict:
        ''' Auxiliary function to StatParser.blkio to remove 'Major' and 'Minor' keys. 
            This function gets only the operations made by blkio counter.
        '''
        ret = dict()
        for d in data:
            ret[d['op'].lower()] = d['value']
        return ret
    
    @staticmethod
    def blkio(data: dict) -> dict:
        ''' Retrieves the blkio counter statistics from a container '''
        ret = dict()
        for key, value in data.items():
            if value:
                value = StatParser._parse_blkio_operations(value)
                for k, v in value.items():
                    ret[f'{key}_{k}'] = v
        return ret

    @staticmethod
    def cpu(data: dict) -> dict:
        ''' Retrieves the cpu counter statistics from a container '''
        name_cpu = lambda x, suffix: {f'cpu{i}_{suffix}': val for i, val in enumerate(x)}
        ret = dict()

        for key, value in data.items():
            if isinstance(value, dict):
                ret[key] = dict()
                for k, v in data[key].items():
                    ret[key][f'cpu_{k}'] = v
            else:
                ret[key] = value

        ret = {
            **name_cpu(data['cpu_usage']['percpu_usage'], 'usage'),
            'system_cpu_usage': data['system_cpu_usage'],
            **data['throttling_data']
        }
        return ret

    @staticmethod
    def memory(data: dict) -> dict:
        ''' Retrieves the memory counter statistics from a container '''
        fields = ['rss', 'cache', 'mapped_file', 'pgpgin', 'pgpgout', 'pgfault', 'pgmajfault', 'active_anon', 'inactive_anon', 'active_file', 'inactive_file', 'unevictable']
        ret = dict()

        for k, v in data.items():
            ret[f'memory_{k}'] = v 
        
        ret = filter_dict(ret, fields)
        return ret
    
    @staticmethod
    def network(data: dict) -> dict:
        ''' Retrieves the network counter statistics from a container '''
        ret = dict()

        # Here it flattens the 'networks' dictionary(ies)
        for net in data:
            for k, v in data[net].items():
                ret[f'net_{net}_{k}'] = v

        return ret

class DockerMonitor(BaseMonitor, Thread):
    def __init__(self, container: Container, pod: Pod, pid: int, kubernetes=True, stats_path="/sys/fs/cgroup", *args, **kwargs):
        self.__container = container
        self.__pid = pid
        self.__pod = pod
        super(DockerMonitor, self).__init__(*args, **kwargs)
        self.__stats_path = stats_path

        if kubernetes:
            self.__pods = Pod.list_pods(namespace="*")

        Thread.__init__(self)

    @property
    def pods(self):
        return self.__pods

    @property
    def stats_path(self):
        return self.__stats_path
    
    @property
    def pid(self) -> int:
        return self.__pid

    @property
    def container(self) -> Container:
        return self.__container
    
    @property
    def pod(self) -> Pod:
        return self.__pod

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
        if pod and container:
            ret = f"{self.stats_path}/{cgroup_controller}/kubepods.slice/kubepods-besteffort.slice/kubepods-besteffort-pod{pod.id}.slice/docker-{container.id}.scope/{cgroup_controller}.{stat}"
        elif container and not pod: 
            ret = f"{self.stats_path}/{cgroup_controller}/system.slice/docker-{container.id}.scope/{cgroup_controller}.{stat}"
        else:
            ret = f"{self.stats_path}/{cgroup_controller}.{stat}"
        
        LOGGER.debug(f"Returned path {ret}")

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

        LOGGER.debug(f"Returned {ret}")

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

        LOGGER.debug(f"Returned {ret}")

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

        LOGGER.debug(f"Selected disk {disk.name} maj:{disk.major} min:{disk.minor}")

        with open(path, mode='r') as fd:
            data = DockerMonitor.parse_fields(list(fd))
                        
        # Filter blkio stats by disk maj:min
        data = filter(lambda x: len(x) == 3, data)
        data = filter(lambda x: x[0] == dev, data)
        data = map(lambda x: x[1:], data)

        LOGGER.debug(f"Returned from 'data = map(lambda x: x[1:], data)': {data}")

        # Map to dict
        ret = {k: v for k, v in data}

        if 'Write' in ret and 'Read' in ret:
            ret['sectors_written'] = int(ret['Write'] / disk.sector_size)
            ret['sectors_read'] = int(ret['Read'] / disk.sector_size)

        return ret

    def get_cpu_times(self, container: Pair=None, pod: Pod=None) -> dict:
        """ 
        Get the CPU usage of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
            _alt_path (str): Alternative path to be gathering data
        """
        path_cpuacct = self.get_path(container=container, pod=pod, cgroup_controller='cpuacct', stat='stat')
        path_cpu = self.get_path(container=container, pod=pod, cgroup_controller='cpu', stat='stat')

        with open(path_cpuacct, mode='r') as fd_cpuacct, open(path_cpu, mode='r') as fd_cpu:
            data = DockerMonitor.parse_fields(list(fd_cpuacct) + list(fd_cpu))

        LOGGER.debug(f"Returned {data}")

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
        ret = ProcessMonitor.get_net_usage(get_container_pid(container))
        
        LOGGER.debug(f"Returned {ret}")

        return ret

    def get_stats(self, container: Pair, pod: Pod=None, disk_name=DEFAULT_DISK_PARTITION) -> dict:
        """ 
        Get all metrics of a given container within a pod 

        Args:
            pod (Pod): Pod container object
            container (Pair): Container pair namedtuple to be monitored
        """
        cpu = self.get_cpu_times(container, pod)
        memory = self.get_memory_usage(container, pod)
        network = self.get_net_usage(container)
        disk = self.get_disk_usage(container, pod, disk_name=disk_name)

        sleep(self.interval)

        cpu_new = subtract_dicts(cpu, self.get_cpu_times(container, pod))
        memory_new = subtract_dicts(memory, self.get_memory_usage(container, pod))
        network_new = subtract_dicts(network, self.get_net_usage(container))
        disk_new = subtract_dicts(disk, self.get_disk_usage(container, pod, disk_name=disk_name))

        ret = {**cpu_new, **memory_new, **network_new, **disk_new}
        
        LOGGER.debug("Called function")

        return ret
    
    def _get_stats(self, *args, **kwargs) -> dict:
        stats = self.container.stats(stream=False)

        ret_old = {
            **StatParser.cpu(stats['cpu_stats']),
            **StatParser.blkio(stats['blkio_stats']),
            **StatParser.memory(stats['memory_stats']),
            **StatParser.network(stats['networks']),
        }

        # Subtracting 2 because the 'container.stats' response takes 1 second to process
        sleep(self.interval - 2)

        stats = self.container.stats(stream=False)

        ret = {
            **StatParser.cpu(stats['cpu_stats']),
            **StatParser.blkio(stats['blkio_stats']),
            **StatParser.memory(stats['memory_stats']),
            **StatParser.network(stats['networks']),
        }

        return subtract_dicts(ret_old, ret)
   
    def run(self) -> None:
        LOGGER.debug(f"Calling method with parameters: container={self.container}, pod={self.pod}, container_pid={get_container_pid(self.container)}")
        self.send(function=self._get_stats, function_args=(self.container, self.pod), container_name=self.container.name, pid=get_container_pid(self.container))
