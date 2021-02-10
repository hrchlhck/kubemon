from subprocess import check_output
from utils import save_csv, subtract_dicts
from threading import Thread
from time import sleep
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

def get_containers(platform):
    if 'win' not in platform:
        return list(filter(lambda c: 'k8s-bigdata' in c.name and 'POD' not in c.name, client.containers.list()))
    return client.containers.list()

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

    ret = {**io_new, **cpu_new, **net_new, "cpu_percent": cpu_percent, "memory": mem_new, "num_fds": num_fds, "open_files": open_files}
    print(ret)
    filename = "%s_%s_%s" % (parent_name, process.pid, process.name())
    save_csv(ret, filename, "process")

def collect(name, pid, interval):
    while True:
        p = psutil.Process(pid=pid)

        if len(p.children()) > 1:
            for child in p.children():
                thread = Thread(target=get_pchild_usage, args=(name, child, interval))
                thread.start()
                sleep(interval)
        else:
            get_pchild_usage(name, child, interval)
            

if __name__ == '__main__':
    client = docker.from_env()
    containers = get_containers(sys.platform)
    container_pids = [(c.name, get_container_pid(c)) for c in containers]
    interval = 5
    for container_name, pid in container_pids:
        print(container_name, pid)
        if 'namenode' in  container_name:
            collect(container_name, pid, interval)
