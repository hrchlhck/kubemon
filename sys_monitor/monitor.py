from .entities.cpu import CPU
from .entities.disk import Disk
from .entities.network import Network
from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET
from .utils import subtract_dicts, send, receive
from .constants import CONNECTION_DIED_CODE
from requests import get
from time import sleep
import psutil


class Monitor:
    def __init__(self, address, port, interval=5, verbose=False):
        self.__interval = interval
        self.__verbose = verbose
        self.__address = address
        self.__port = port

    def __get_data(self):
        disk = Disk().get_usage()
        cpu = CPU().get_usage
        net = Network().get_usage
        mem = psutil.virtual_memory().percent
        loadavg = psutil.getloadavg()
        data = {
            **cpu,
            "memory_usage": mem,
            **net,
            **disk.infos,
            "loadavg_1min": loadavg[0],
            "loadavg_5min": loadavg[1],
            "loadavg_15min": loadavg[2]
        }
        
        return data

    def __calc_usage(self, interval):
        data = self.__get_data()

        sleep(interval)
        
        data_new = self.__get_data()
        
        return subtract_dicts(data, data_new)

    def start(self):
        send(self.__address, self.__port, self.__calc_usage, self.__interval, "sys")
