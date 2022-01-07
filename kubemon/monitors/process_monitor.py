from threading import Thread

from docker.models.containers import Container
from ..utils import subtract_dicts, get_host_ip
from .base_monitor import BaseMonitor
from ..log import create_logger
import psutil
import os
import socket


def parse_proc_net(pid):
    # Assert if pid exists in /proc
    assert str(pid) in os.listdir('/proc')

    def to_dict(cols, vals):
        return {k: v for k, v in zip(cols, vals)}

    fd = "/proc/%s/net/dev" % pid
    with open(fd, mode='r') as f:
        lines = f.readlines()

        # Parse column names
        cols = list(map(lambda x: x.split(), lines[1].split('|')))
        shift_factor = 9

        for line in lines[2:]:
            # Parsed values
            aux = list(
                map(lambda x: int(x) if x.isdigit() else x, line.split()))

            iface = aux[0].replace(':', '')
            rx = to_dict(cols[1], aux[1:shift_factor])
            tx = to_dict(cols[2], aux[shift_factor:])
            ret = {'iface': iface, 'rx': rx, 'tx': tx}
            yield ret

LOGGER = create_logger(__name__)

class ProcessMonitor(BaseMonitor, Thread):
    def __init__(self, container: Container, pid: int, *args, **kwargs):
        self.__container = container
        self.__pid = pid
        super(ProcessMonitor, self).__init__(*args, **kwargs)
        Thread.__init__(self)

    @property
    def pid(self) -> int:
        return self.__pid

    @property
    def container(self) -> Container:
        return self.__container

    def __str__(self) -> str:
        return f'<{self.name} - {socket.gethostname()} - {get_host_ip()} - {self.__container.name} - {self.__pid}>'
    
    def __repr__(self) -> str:
        return f'<{self.name} - {socket.gethostname()} - {get_host_ip()} - {self.__container.name} - {self.__pid}>'

    @staticmethod
    def get_cpu_times(process: psutil.Process) -> dict:
        """ 
        Returns the CPU usage by a process. 

        Args:
            process (psutil.Process): The process that you want to get the data
        """
        ret = dict()
        cpu_data = process.cpu_times()
        ret['cpu_user'] = cpu_data.user
        ret['cpu_system'] = cpu_data.system
        ret['cpu_children_user'] = cpu_data.children_user
        ret['cpu_children_system'] = cpu_data.children_system
        ret['cpu_iowait'] = cpu_data.iowait

        return ret

    @staticmethod
    def get_io_counters(process: psutil.Process) -> dict:
        """ 
        Returns the disk usage by a process

        Args:
            process (psutil.Process): The process that you want to get the data
        """
        ret = dict()
        io_counters = process.io_counters()
        ret['io_read_count'] = io_counters.read_count
        ret['io_write_count'] = io_counters.write_count
        ret['io_read_bytes'] = io_counters.read_bytes
        ret['io_write_bytes'] = io_counters.write_bytes
        ret['io_read_chars'] = io_counters.read_chars
        ret['io_write_chars'] = io_counters.write_chars

        return ret

    @staticmethod
    def get_net_usage(pid: int, iface='eno0') -> dict:
        """ 
        Returns the network usage by a process 

        Args:
            pid (int): The pid of the process
            iface (str): The network interface that you want to get the usage
        """
        # Network interface
        nic = [nic for nic in parse_proc_net(pid) if nic['iface'] == iface]
        
        if len(nic) == 0:
            return {'rx_bytes': 0, 'rx_packets': 0, 'tx_bytes': 0, 'tx_packets': 0}

        nic = nic[0]
        
        ret = dict()
        ret['rx_bytes'] = nic['rx']['bytes']
        ret['rx_packets'] = nic['rx']['packets']
        ret['tx_bytes'] = nic['tx']['bytes']
        ret['tx_packets'] = nic['tx']['packets']

        return ret

    @classmethod
    def get_pchild_usage(cls: object, interval: int, pid: int) -> dict:
        """
        Merges all dicts returned by the static methods from this class and returns a new dict

        Args:
            process (int): The PID of the process that you want to get the data
            interval (int): The seconds that the script will calculate the usage
        """
        process = psutil.Process(pid=pid)
        cpu = cls.get_cpu_times(process)
        io = cls.get_io_counters(process)
        mem = BaseMonitor.get_memory_usage(pid=pid)
        net = cls.get_net_usage(process.pid)

        # Acts as time.sleep()
        cpu_percent = process.cpu_percent(interval=interval)

        io_new = subtract_dicts(io, cls.get_io_counters(process))
        cpu_new = subtract_dicts(cpu, cls.get_cpu_times(process))
        mem_new = subtract_dicts(mem, BaseMonitor.get_memory_usage(pid=pid))
        net_new = subtract_dicts(net, cls.get_net_usage(process.pid))

        ret = {**io_new, **cpu_new, **net_new, "cpu_percent": cpu_percent, **mem_new}
        return ret

    def run(self) -> None:
        self.send(function=self.get_pchild_usage, function_args=(self.interval, self.pid), pid=self.pid, container_name=self.container.name)

