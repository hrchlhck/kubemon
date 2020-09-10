import psutil
import time
import json
import requests


class Monitor:
    def __init__(self, address, port, interval=1, verbose=False):
        self.__interval = interval
        self.__verbose = verbose
        self.__address = "http://" + address + ":" + str(port)

    def __get_data(self):
        swap = psutil.swap_memory().percent
        swap_enabled = swap != 0
        mem = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        net_usage = net_usage = net_io.bytes_sent + net_io.bytes_recv
        return {
            "cpu_usage": cpu,
            "memory_usage": mem,
            "disk_read_bytes": disk_io.read_bytes,
            "disk_written_bytes": disk_io.write_bytes,
            "net_usage": net_usage,
            "swap_enabled": swap_enabled,
            "swap": swap,
        }

    def start(self):
        if not self.__verbose:
            print("Running on silent mode\n")

        prev_net = 0
        total_net = 0

        while True:
            data = self.__get_data()

            actual_net = data["net_usage"]

            if prev_net:
                total_net = actual_net - prev_net

            prev_net = actual_net
            
            data["net_usage"] = total_net

            if self.__verbose:
                print(f'\nCPU: {data["cpu_usage"]}')
                print(f'Memory: {data["memory_usage"]}')
                print(f'Disk read: {data["disk_read_bytes"]}')
                print(f'Disk write: {data["disk_written_bytes"]}')
                print(f'Net usage: {data["net_usage"]}')
                print(f'Swap enabled?: {data["swap_enabled"]}')

                if data["swap_enabled"]:
                    print(f"Swap: {data['swap']}")

            requests.post(self.__address, json=json.dumps(data))

            time.sleep(self.__interval)
