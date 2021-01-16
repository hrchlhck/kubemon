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
        self.__cpu = CPU()
        self.__disk = Disk()
        self.__network = Network()

    def __get_data(self):
        disk = self.__disk.get_info()
        cpu = self.__cpu.get_info(self.__interval)
        net = self.__network.get_info()
        mem = psutil.virtual_memory().percent
        data = {
            "cpu_usage": cpu,
            "memory_usage": mem,
            "dsk_sectors_read": disk["sectors_read"],
            "dsk_sectors_write": disk["sectors_written"],
            "bytes_sent": net["bytes_sent"],
            "bytes_recv": net["bytes_recv"],
            "packets_sent": net["packets_sent"],
            "packets_recv": net["packets_recv"],
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
            _socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            _socket.connect((self.__address, self.__port))
            print(f"Connected monitor to collector")
            
            signal = _socket.recv(1024).decode("utf8")

            if signal and signal == "start":
                print("Starting monitor")

                try:
                    while True:
                        data = self.__calc_usage()
                        
                        if self.__verbose:
                            print(data)

                        send_data(_socket, data, "sys_monitor")
                except:
                    _socket.send(CONNECTION_DIED_CODE.encode("utf-8"))
                    _socket.close()
