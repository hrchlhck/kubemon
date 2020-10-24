from requests.exceptions import ConnectionError
from .entities.cpu import CPU
from .entities.disk import Disk
from .entities.network import Network
from .utils import subtract_dicts
from time import sleep
import json
import requests
import psutil


class Monitor:
    def __init__(self, address, port, interval=5, verbose=False):
        self.__interval = interval
        self.__verbose = verbose
        self.__address = f"http://{address}:{port}"
        self.__cpu = CPU()
        self.__disk = Disk()
        self.__network = Network()
        self.__header = {"from": "sys_monitor"}

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
        sleep(self.__interval)      
        
        if not self.__verbose:
            print("Running on silent mode\n")

        while True:
            temp = self.__calc_usage()
            
            if self.__verbose:
                print(temp)

            try:
                requests.post(self.__address, json=json.dumps(temp), headers=self.__header)
            except ConnectionError:
                print('Connection refused.')
