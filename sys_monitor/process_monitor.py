from subprocess import check_output
from .utils import save_csv, subtract_dicts, send_data, CONNECTION_DIED_CODE, format_name, get_containers
from threading import Thread
from time import sleep
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
import psutil
import docker
import sys
import os

def get_container_pid(container):
    cmd = ['docker', 'inspect', '-f', '{{.State.Pid}}', container.id]
    return int(check_output(cmd))

def subtract_tuple(tup1, tup2):
    assert len(tup1) == len(tup2)
    return tuple(round(tup1[i] - tup2[i], 4) for i in range(len(tup1)))

def get_cpu_times(process):
    ret = dict()
    cpu_data = process.cpu_times()
    ret['cpu_user'] = cpu_data.user
    ret['cpu_system'] = cpu_data.system
    ret['cpu_children_user'] = cpu_data.children_user
    ret['cpu_children_system'] = cpu_data.children_system
    ret['cpu_iowait'] = cpu_data.iowait
    return ret

def get_io_counters(process):
    ret = dict()
    io_counters = process.io_counters()
    ret['io_read_count'] = io_counters.read_count
    ret['io_write_count'] = io_counters.write_count
    ret['io_read_bytes'] = io_counters.read_bytes
    ret['io_write_bytes'] = io_counters.write_bytes
    ret['io_read_chars'] = io_counters.read_chars
    ret['io_write_chars'] = io_counters.write_chars
    return ret

def parse_proc_net(pid):
    # Assert if platform is not windows
    assert 'win' not in sys.platform

    # Assert if pid exists in /proc
    assert str(pid) in os.listdir('/proc')

    def to_dict(cols, vals):
        return {k:v for k,v in zip(cols, vals)}

    fd = "/proc/%s/net/dev" % pid
    with open(fd, mode='r') as f:
        lines = f.readlines()

        # Parse column names
        cols = list(map(lambda x: x.split(), lines[1].split('|')))
        shift_factor = 9

        for line in lines[2:]:
            # Parsed values
            aux = list(map(lambda x: int(x) if x.isdigit() else x, line.split()))

            iface = aux[0].replace(':', '')
            rx = to_dict(cols[1], aux[1:shift_factor])
            tx = to_dict(cols[2], aux[shift_factor:])
            ret = {'iface': iface, 'rx': rx, 'tx': tx}
            yield ret

def get_net_usage(pid, iface='eth0'):
    # Network interface
    nic = list(nic for nic in parse_proc_net(pid) if nic['iface'] == iface)[0]
    ret = dict()
    ret['rx_bytes'] = nic['rx']['bytes']
    ret['rx_packets'] = nic['rx']['packets']
    ret['tx_bytes'] = nic['tx']['bytes']
    ret['tx_packets'] = nic['tx']['packets']
    return ret

def get_pchild_usage(parent_name, process, interval):
    cpu = get_cpu_times(process)
    io = get_io_counters(process)
    mem = process.memory_percent(memtype='rss')
    num_fds = process.num_fds()
    net = get_net_usage(process.pid)

    open_files = len(process.open_files())
    
    cpu_percent = process.cpu_percent(interval=interval)
    
    io_new = subtract_dicts(io, get_io_counters(process))
    cpu_new = subtract_dicts(cpu, get_cpu_times(process))
    mem_new = round(process.memory_percent(memtype='rss') - mem, 4)
    num_fds = process.num_fds() - num_fds
    net_new = subtract_dicts(net, get_net_usage(process.pid))
    open_files = len(process.open_files()) - open_files

    ret = {**io_new, **cpu_new, **net_new, "cpu_percent": cpu_percent, "memory": mem_new, "num_fds": num_fds, "open_files": open_files}
    return ret

def parallel_send(parent_name, process, interval, addr, port):
    with socket(AF_INET, SOCK_STREAM) as _socket:
        buffer_size = 1024
        _socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        _socket.connect((addr, port))
        print("Connected process %s collector to server" % format_name(parent_name))
        
        signal = _socket.recv(buffer_size).decode("utf8")

        if signal and signal == "start":
            print("Starting monitor")

            while True:
                ret = get_pchild_usage(parent_name, process, interval)
                send_data(_socket, ret, "process_collector_%s_%s" % (format_name(parent_name), process.pid))
                print(ret)
                print(_socket.recv(1024).decode("utf8"))

def collect(name, pid, interval, addr, port):
    with socket(AF_INET, SOCK_STREAM) as _socket:
        buffer_size = 1024
        _socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        _socket.connect((addr, port))
        print("Connected process %s collector to server" % name)
        
        p = psutil.Process(pid=pid)

        if len(p.children()) > 1:
            for child in p.children():
                Thread(target=parallel_send, args=(name, child, interval, addr, port)).start()

        signal = _socket.recv(buffer_size).decode("utf8")


        if signal and signal == "start":
            print("Starting monitor")

            try:
                while True:
                    ret = get_pchild_usage(name, p, interval)
                    send_data(_socket, ret, "process_collector_%s_%s" % (format_name(name), p.pid))
                    print(_socket.recv(buffer_size).decode("utf8"))
            except:
                send_data(_socket, CONNECTION_DIED_CODE, "process_collector")
                _socket.close()
            

class ProcessMonitor:
    def __init__(self, address, port, interval=5):
        self.__address = address
        self.__port = port
        self.__interval = interval

    def start(self):
        client = docker.from_env()
        containers = get_containers(client, sys.platform)
        container_pids = [(c.name, get_container_pid(c)) for c in containers]
        
        for container_name, pid in container_pids:
            t = Thread(target=collect, args=(container_name, pid, self.__interval, self.__address, self.__port))
            t.start()