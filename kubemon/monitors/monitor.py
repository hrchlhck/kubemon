from kubemon.config import DEFAULT_DISK_PARTITION
from .base_monitor import BaseMonitor
from ..entities.cpu import CPU
from ..entities.disk import Disk
from ..entities.network import Network
from ..utils import subtract_dicts
import time


class OSMonitor(BaseMonitor):
    def __init__(self, *args, **kwargs):
        super(OSMonitor, self).__init__(*args, **kwargs)
        
    def __get_data(self):
        disk = Disk(disk_name=DEFAULT_DISK_PARTITION).get_usage()
        cpu = CPU().get_usage
        net = Network().get_usage
        mem = BaseMonitor.get_memory_usage()
        data = {
            **cpu,
            **mem,
            **disk.infos,
            **net,
        }

        return data

    def collect(self):
        data = self.__get_data()

        time.sleep(self.interval)

        data_new = self.__get_data()

        ret = subtract_dicts(data, data_new)

        return ret

    def start(self):
        super(OSMonitor, self).start()
