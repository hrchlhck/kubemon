import psutil
import time
import json
import requests


class Monitor:
    def __init__(self, address, port, interval=1, verbose=False):
        self.__interval = interval
        self.__csv_header = [
            "cpu_usage",
            "memory_usage",
            "disk_read_bytes",
            "disk_written_bytes",
            "net_sent_bytes",
            "net_received_bytes",
            "net_sent_packets",
            "net_received_packets",
            "swap_enabled",
            "swap",
        ]
        self.__verbose = verbose
        self.__address = "http://" + address + ":" + str(port)

    def __get_data(self):
        swap = psutil.swap_memory().percent
        swap_enabled = swap != 0
        mem = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        return {
            "cpu_usage": cpu,
            "memory_usage": mem,
            "disk_read_bytes": disk_io.read_bytes,
            "disk_written_bytes": disk_io.write_bytes,
            "net_sent_bytes": net_io.bytes_sent,
            "net_received_bytes": net_io.bytes_recv,
            "net_sent_packets": net_io.packets_sent,
            "net_received_packets": net_io.packets_recv,
            "swap_enabled": swap_enabled,
            "swap": swap,
        }

    def start(self):
        if not self.__verbose:
            print("Running on silent mode\n")

        while True:
            data = self.__get_data()

            if self.__verbose:
                print(f'\nCPU: {data["cpu_usage"]}')
                print(f'Memory: {data["memory_usage"]}')
                print(f'Disk read: {data["disk_read_bytes"]}')
                print(f'Disk write: {data["disk_written_bytes"]}')
                print(f'Net sent: {data["net_sent_bytes"]}')
                print(f'Net received: {data["net_received_bytes"]}')
                print(f'Net sent pkg: {data["net_sent_packets"]}')
                print(f'Net received pkg: {data["net_received_packets"]}')
                print(f'Swap enabled?: {data["swap_enabled"]}')

                if data["swap_enabled"]:
                    print(f"Swap: {data['swap']}")

            requests.post(self.__address, json=json.dumps(data))

            time.sleep(self.__interval)
