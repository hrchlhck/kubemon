from ..utils import get_host_ip, filter_dict

from ..log import create_logger

import socket
import os

LOGGER = create_logger(__name__)

class BaseMonitor:
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
                infos = list(map(lambda x: 'mem_' + x, infos))
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
        name = self.__class__.__name__
        parse_ip = lambda ip: ip.replace(".", "_")
        ip = parse_ip(get_host_ip())
        ret = f"{name}_{ip}_{socket.gethostname()}_{pid}"

        if name == "ProcessMonitor" or name == "DockerMonitor":
            ret = f"{name}_{ip}_{socket.gethostname()}_{container_name}_{pid}"
        
        LOGGER.debug(f"Got name {ret}")

        return ret
