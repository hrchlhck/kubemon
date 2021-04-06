from .base_monitor import BaseMonitor
from .entities.cpu import CPU
from .entities.disk import Disk
from .entities.network import Network
from .utils import subtract_dicts
from time import sleep
import psutil


class OSMonitor(BaseMonitor):
    def __init__(self, *args, **kwargs):
        super(OSMonitor, self).__init__(*args, **kwargs)

    def __get_data(self):
        disk = Disk(disk_name='sda').get_usage()
        cpu = CPU().get_usage
        net = Network().get_usage
        mem = BaseMonitor.get_memory_usage()
        data = {
            **cpu,
            **mem,
            **net,
            **disk.infos,
        }

        return data

    def collect(self, interval):
        data = self.__get_data()
        sleep(interval)

        data_new = self.__get_data()

        ret = subtract_dicts(data, data_new)

        loadavg = psutil.getloadavg()
        ret['loadavg_1min'] = loadavg[0]
        ret['loadavg_5min'] = loadavg[1]
        ret['loadavg_15min'] = loadavg[2]

        return ret

    def start(self):
        super(OSMonitor, self).start()
