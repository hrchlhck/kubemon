from .entities.cpu import CPU
from .entities.disk import Disk
from .entities.network import Network
from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET
from .utils import subtract_dicts, send_data, CONNECTION_DIED_CODE
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

    def __calc_usage(self):
        data = self.__get_data()

        sleep(self.__interval)
        
        data_new = self.__get_data()
        
        return subtract_dicts(data, data_new)

    def start(self):
        if not self.__verbose:
            print("Running on silent mode\n")

        with socket(AF_INET, SOCK_STREAM) as _socket:
            buffer_size = 1024
            _socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            _socket.connect((self.__address, self.__port))
            print("Connected monitor to collector")
            
            signal = _socket.recv(buffer_size).decode("utf8")

            if signal and signal == "start":
                print("Starting monitor")

                try:
                    while True:
                        data = self.__calc_usage()
                        
                        if self.__verbose:
                            print(data)

                        send_data(_socket, data, "sys_wide_monitor")
                        print(_socket.recv(buffer_size).decode("utf8"))
                except:
                    send_data(_socket, CONNECTION_DIED_CODE, "sys_wide_monitor")
                    _socket.close()
