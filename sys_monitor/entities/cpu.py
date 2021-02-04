from psutil import cpu_times as cpu
from psutil import getloadavg as loadavg
from .base_entity import BaseEntity


class CPU(BaseEntity):
    """ Represents an CPU object that returns CPU usage of a system """
    def __get_busy_time(self):
        c = cpu()
        return c.user + c.system + c.irq + c.softirq + c.nice 

    @property
    def get_usage(self):
        return round(self.__get_busy_time(), 4)
    
    @property
    def get_loadavg(self):
        return loadavg()

