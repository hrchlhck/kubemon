from threading import Thread
from logging import Logger
from datetime import datetime
from time import sleep
from os.path import join as join_path

from kubemon.settings import MONITOR_PORT, START_MESSAGE, COLLECT_INTERVAL, DATA_PATH, COLLECT_TASK_PORT
from kubemon.utils.data import save_csv, subtract_dicts, in_both
from kubemon.utils.networking import receive

import requests
import socket

class MonitorHandler(Thread):
    def __init__(self, monitor_address: str, monitor_name: str, collector: object):
        self._addr = monitor_address
        self._monitor_name = monitor_name
        self._collector = collector
        self._logger = collector.logger

        Thread.__init__(self)
    
    def __str__(self) -> str:
        return self._monitor_name

    @property
    def _log(self):
        if not self._logger:
            return
        
        if not isinstance(self._logger, Logger):
            raise TypeError('Must specify a logging.Logger object')
        
        return self._logger

    def run(self) -> None:
        name = self._monitor_name
        addr = self._addr
        self._log.info(f"Starting MonitorHandler for {name}@{addr}")
        monitor_url = f'https://{self._addr}:{MONITOR_PORT}'
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
            sockfd.connect((self._collector.address, COLLECT_TASK_PORT))

            if not self._collector.metric_paths:
                req = requests.get(monitor_url).json()

                with self._collector.mutex:
                    self.metric_paths = req['metric_paths']

            while True:

                msg, _ = receive(sockfd)
                self._log.info('Received message: %s' % msg)

                if msg == START_MESSAGE:
                    while not self._collector.stop_request:
                        if self._collector.stop_request:
                            self._log.info(f'Stopped for {name}@{addr}')
                            break

                        old_data = requests.get(monitor_url).json()

                        sleep(COLLECT_INTERVAL)
                        
                        new_data = requests.get(monitor_url).json()

                        for k in in_both(old_data, new_data):
                            ret = subtract_dicts(old_data[k], new_data[k])
                            ret['timestamp'] = datetime.now()

                            if self.dir_name:
                                dir_name = join_path(self._collector.dir_name, k.split("_")[0])

                            save_csv(ret, k, dir_name=dir_name)
                            self._log.info(f"Saving data to {str(DATA_PATH)}/{self.dir_name}/{k}")

                            if self._collector.stop_request:
                                self._collector.event.set()
    
