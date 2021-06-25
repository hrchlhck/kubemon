from psutil import cpu_times, cpu_stats
from addict import Dict
from .base_entity import BaseEntity


class CPU(BaseEntity):
    """ Represents an CPU object that returns CPU usage of a system """

    def __init__(self):
        self.__infos = Dict()

    def __set_data(self):
        # Cpu stats
        self.__infos.cpu_stat_ctx_switches = cpu_stats().ctx_switches
        self.__infos.cpu_stat_interrupts = cpu_stats().interrupts
        self.__infos.cpu_stat_soft_interrupts = cpu_stats().soft_interrupts
        self.__infos.cpu_stat_syscalls = cpu_stats().syscalls

        # Cpu times
        self.__infos.cpu_times_user = cpu_times().user
        self.__infos.cpu_times_system = cpu_times().system
        self.__infos.cpu_times_nice = cpu_times().nice
        self.__infos.cpu_times_softirq = cpu_times().softirq
        self.__infos.cpu_times_irq = cpu_times().irq
        self.__infos.cpu_times_iowait = cpu_times().iowait
        self.__infos.cpu_times_guest = cpu_times().guest
        self.__infos.cpu_times_guest_nice = cpu_times().guest_nice
        self.__infos.cpu_times_idle = cpu_times().idle

    @property
    def get_usage(self):
        self.__set_data()
        return self.__infos
