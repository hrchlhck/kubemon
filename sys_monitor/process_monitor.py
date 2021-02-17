from .utils import subtract_dicts, get_containers, get_container_pid, send
from threading import Thread
from time import sleep
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
import psutil
import docker
import sys
import os


def parse_proc_net(pid):
    # Assert if platform is not windows
    assert 'win' not in sys.platform

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


class ProcessMonitor:
    def __init__(self, address, port, interval=5):
        self.__address = address
        self.__port = port
        self.__interval = interval

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
    def get_net_usage(pid: int, iface='eth0') -> dict:
        """ 
        Returns the network usage by a process 

        Args:
            pid (int): The pid of the process
            iface (str): The network interface that you want to get the usage
        """
        # Network interface
        nic = list(nic for nic in parse_proc_net(
            pid) if nic['iface'] == iface)[0]
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
        mem = process.memory_percent(memtype='rss')
        num_fds = process.num_fds()
        net = cls.get_net_usage(process.pid)

        open_files = len(process.open_files())

        cpu_percent = process.cpu_percent(interval=interval)

        io_new = subtract_dicts(io, cls.get_io_counters(process))
        cpu_new = subtract_dicts(cpu, cls.get_cpu_times(process))
        mem_new = round(process.memory_percent(memtype='rss') - mem, 4)
        num_fds = process.num_fds() - num_fds
        net_new = subtract_dicts(net, cls.get_net_usage(process.pid))
        open_files = len(process.open_files()) - open_files

        ret = {**io_new, **cpu_new, **net_new, "cpu_percent": cpu_percent,
               "memory": mem_new, "num_fds": num_fds, "open_files": open_files}
        return ret

    def collect(self, container_name: str, pid: int) -> None:
        """ 
        Method to collects all data from all container processes

        Args:
            container_name (str): Container name
            pid (int): Pid of the container process

        """
        process = psutil.Process(pid=pid)

        for child in process.children():
            args = (self.__address, self.__port, self.get_pchild_usage,
                    self.__interval, "process_monitor", container_name, child.pid)
            t = Thread(target=send, args=args)
            t.start()

    def start(self) -> None:
        """ Method to start ProcessMonitor """
        client = docker.from_env()
        containers = get_containers(client, sys.platform)
        container_pids = [(c.name, get_container_pid(c)) for c in containers]

        for container_name, pid in container_pids:
            t = Thread(target=self.collect, args=(container_name, pid))
            t.start()
