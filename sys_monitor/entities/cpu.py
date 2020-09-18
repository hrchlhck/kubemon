from psutil import cpu_times as cpu
from platform import platform


class CPU:
    __platform = platform.platform()

    def __get_busy_time(self):
        platform = self.__platform
        c = cpu()
        if "Windows" in platform:
            return c.user + c.system + c.interrupt + c.dpc
        elif "Linux" in platform:
            return c.user + c.system + c.iowait + c.irq + c.softirq + c.nice

    def get_time(self):
        c = cpu()
        idle = c.idle
        busy = self.__get_busy_time()
        total = busy + idle
        return busy / total * 100
