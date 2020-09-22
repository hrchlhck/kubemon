from .entities.cpu import CPU
from .entities.disk import Disk
from json import dumps
from time import sleep
from requests import post
import psutil


class Monitor:
    def __init__(self, address, port, interval=5, verbose=False):
        self.__interval = interval
        self.__verbose = verbose
        self.__address = "http://" + address + ":" + str(port)
        self.__cpu = CPU()
        self.__disk = Disk()

    def __get_data(self):
        disk = self.__disk.get_info()
        cpu = self.__cpu.get_info()
        mem = psutil.virtual_memory().percent
        swap = psutil.swap_memory().used
        swap_enabled = swap != 0
        data = {
            "cpu_usage": cpu,
            "memory_usage": mem,
            "dsk_sectors_rd": disk["sectors_read"],
            "dsk_sectors_wrt": disk["sectors_written"],
        }

        if swap_enabled:
            data["swap"] = swap

        return data

    def start(self):
        if not self.__verbose:
            print("Running on silent mode\n")

        data = self.__get_data()
        cpu_usage = data["cpu_usage"]
        memory_usage = data["memory_usage"]
        disk_read_avg = data["disk_read_avg"]

        while True:
            data = self.__get_data()

            cpu_new = data["cpu_usage"]
            memory_new = data["memory_usage"]
            disk_read_new = data["disk_read_avg"]
            disk_write_new = data["disk_write_avg"]

            sleep(self.__interval)

            cpu_usage = round(cpu_new - cpu_usage, 4)
            memory_usage = round(memory_new - memory_usage, 4)
            disk_read_avg = round(disk_read_new - disk_read_avg, 4)
            disk_write_avg = round(disk_write_new - disk_write_avg, 4)

            if self.__verbose:
                print(f"\nCPU: {cpu_usage}")
                print(f"Memory: {memory_usage}")
                print(f"Disk read: {disk_read_avg}")
                print(f"Disk write: {disk_write_avg}")

                if "swap" in data.keys():
                    print(f"Swap: {data['swap']}")

            post(self.__address, json=dumps(data))
