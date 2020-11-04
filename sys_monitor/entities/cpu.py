from psutil import cpu_times as cpu
from .base_entity import BaseEntity


class CPU(BaseEntity):
    """ Represents an CPU object that returns CPU usage of a system """
    def __get_busy_time(self):
        c = cpu()
        return c.user + c.system + c.irq + c.softirq + c.nice

    def get_info(self, interval):
        return round(self.__get_busy_time() / interval, 4)
