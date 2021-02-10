from addict import Dict
from .utils import subtract_dicts, send_data, CONNECTION_DIED_CODE, format_name, get_containers
from .process_monitor import get_container_pid, parse_proc_net
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
import docker
import threading
import time
import os
import sys

# Refer to https://docs.docker.com/config/containers/runmetrics/ for more information
class Stats:
    @staticmethod
    def get_cpu_usage(container):
        usage = Dict(container.stats(stream=False)).cpu_stats
        ret = Dict()
        ret.total_usage = usage.cpu_usage.total_usage
        ret.kernel = usage.cpu_usage.usage_in_kernelmode
        ret.user = usage.cpu_usage.usage_in_usermode
        ret.system = usage.system_cpu_usage
        return ret.to_dict()
    
    @staticmethod
    def get_memory_usage(container):
        mem = Dict(container.stats(stream=False)).memory_stats
        ret = Dict()
        ret.usage = mem.usage
        ret.rss = mem.stats.rss
        ret.cache = mem.stats.cache
        ret.mapped_file = mem.stats.mapped_file
        ret.active_file = mem.stats.active_file
        ret.inactive_file = mem.stats.inactive_file
        ret.active_anon = mem.stats.active_anon
        ret.inactive_anon = mem.stats.inactive_anon
        ret.pgfault = mem.stats.pgfault
        ret.pgmajfault = mem.stats.pgmajfault
        return ret.to_dict()

    @staticmethod
    def get_network_usage(container, iface='eth0'):
        net = parse_proc_net(get_container_pid(container))
        net = Dict([nic for nic in net if nic['iface'] == iface][0])
        ret = Dict()
        ret.rx_bytes = net.rx.bytes
        ret.rx_packets = net.rx.packets
        ret.tx_bytes = net.tx.bytes
        ret.tx_packets = net.tx.packets
        return ret.to_dict()
    
    @staticmethod
    def get_block_io(container):
        blkio = Dict(container.stats(stream=False)).blkio_stats
        ret = Dict()
        ret.bytes_read = blkio.io_service_bytes_recursive[0]['value']
        ret.bytes_write = blkio.io_service_bytes_recursive[1]['value']
        ret.bytes_sync = blkio.io_service_bytes_recursive[2]['value']
        ret.bytes_async = blkio.io_service_bytes_recursive[3]['value']
        ret.bytes_discard = blkio.io_service_bytes_recursive[4]['value']
        return ret.to_dict()
    
    @classmethod
    def get_stats(cls, container, interval):
        old = dict(
            **cls.get_cpu_usage(container),
            **cls.get_network_usage(container),
            **cls.get_memory_usage(container),
            **cls.get_block_io(container)
        )
        time.sleep(interval)
        new = dict(
            **cls.get_cpu_usage(container),
            **cls.get_network_usage(container),
            **cls.get_memory_usage(container),
            **cls.get_block_io(container)
        )
        return subtract_dicts(old, new)

def collect(container, interval, addr, port):
    with socket(AF_INET, SOCK_STREAM) as _socket:
        buffer_size = 1024
        _socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        _socket.connect((addr, port))
        print("Connected docker %s collector to server" % format_name(container.name))
        
        signal = _socket.recv(buffer_size).decode("utf8")

        if signal and signal == "start":
            print("Starting monitor")

            while True:
                ret = Stats.get_stats(container, interval)
                send_data(_socket, ret, "docker_collector_%s" % (format_name(container.name)))
                print(ret)
                print(_socket.recv(buffer_size).decode("utf8"))
    
class DockerMonitor:
    def __init__(self, address, port, interval=5):
        self.__address = address
        self.__port = port
        self.__interval = interval

    def start(self):
        client = docker.from_env()
        for container in get_containers(client, sys.platform):
            t = threading.Thread(target=collect, args=(container, self.__interval, self.__addr, self.__port))
            t.start()
        