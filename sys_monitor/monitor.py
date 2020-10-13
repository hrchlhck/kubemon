from requests.exceptions import ConnectionError
from .entities.cpu import CPU
from .entities.disk import Disk
from .entities.network import Network
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

    def __get_data(self):
        disk = self.__disk.get_info()
        cpu = self.__cpu.get_info(self.__interval)
        net = self.__network.get_info()
        mem = psutil.virtual_memory().percent
        swap = psutil.swap_memory().used
        swap_enabled = swap != 0
        data = {
            "cpu_usage": cpu,
            "memory_usage": mem,
            "dsk_sectors_rd": disk["sectors_read"],
            "dsk_sectors_wrt": disk["sectors_written"],
            "bytes_sent": net["bytes_sent"],
            "bytes_recv": net["bytes_recv"],
            "packets_sent": net["packets_sent"],
            "packets_recv": net["packets_recv"],
        }

        if swap_enabled:
            data["swap"] = swap

        return data

    def __calc_usage(self):
        data = self.__get_data()

        cpu_usage = data["cpu_usage"]
        memory_usage = data["memory_usage"]
        disk_read_avg = data["dsk_sectors_rd"]
        disk_write_avg = data["dsk_sectors_wrt"]
        bytes_sent = data["bytes_sent"]
        bytes_recv = data["bytes_recv"]
        packets_recv = data["packets_recv"]
        packets_sent = data["packets_sent"]

        sleep(self.__interval)
        
        data = self.__get_data()
        cpu_new = data["cpu_usage"]
        memory_new = data["memory_usage"]
        disk_read_new = data["dsk_sectors_rd"]
        disk_write_new = data["dsk_sectors_wrt"]
        bytes_sent_new = data["bytes_sent"]
        bytes_recv_new = data["bytes_recv"]
        packets_recv_new = data["packets_recv"]
        packets_sent_new = data["packets_sent"]

        cpu_usage = round(cpu_new - cpu_usage, 4)
        memory_usage = round(memory_new - memory_usage, 4)
        disk_read_avg = round(disk_read_new - disk_read_avg, 4)
        disk_write_avg = round(disk_write_new - disk_write_avg, 4)
        bytes_recv = round(bytes_recv_new - bytes_recv, 4)
        bytes_sent = round(bytes_sent_new - bytes_sent, 4)
        packets_recv = round(packets_recv_new - packets_recv, 4)
        packets_sent = round(packets_sent_new - packets_sent, 4)

        return (cpu_usage, memory_usage, disk_read_avg, disk_write_avg, bytes_recv, bytes_sent, packets_recv, packets_sent)

    def start(self):
        header = {"from": "sys_monitor"}
        
        if not self.__verbose:
            print("Running on silent mode\n")

        while True:
            temp = self.__calc_usage()

            data = {
                "cpu_usage": temp[0],
                "memory_usage": temp[1],
                "disk_read_avg": temp[2],
                "disk_write_avg": temp[3],
                "bytes_recv": temp[4],
                "bytes_sent": temp[5],
                "packets_sent": temp[6],
                "packets_recv": temp[7],
            }

            if self.__verbose:
                print(f"\nCPU: {temp[0]}")
                print(f"Memory: {temp[1]}")
                print(f"Disk sectors read: {temp[2]}")
                print(f"Disk sectors written: {temp[3]}")
                print(f"Net bytes sent: {temp[4]}")
                print(f"Net bytes recv: {temp[5]}")
                print(f"Net pkt sent: {temp[6]}")
                print(f"Net pkt recv: {temp[7]}")

            try:
                requests.post(self.__address, json=json.dumps(data), headers=header)
            except ConnectionError:
                print('Connection refused.')
