from threading import Thread
from logging import Logger
from datetime import datetime
from time import sleep
from os.path import join as join_path
from typing import Any, Dict, List

from kubemon.settings import START_MESSAGE, COLLECT_INTERVAL
from kubemon.utils.data import save_csv, subtract_dicts, in_both
from kubemon.utils.networking import receive, send_to, get_json


import socket

class MonitorHandler(Thread):
    def __init__(self, monitor_address: str, monitor_name: str, collector: object):
        self._addr = monitor_address
        self._monitor_name = monitor_name
        self._collector = collector
        self._logger = collector.logger

        self.paths = ""

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

    def _collect_per_path(self, paths: List[str]) -> Dict[str, Dict[str, Any]]:
        result = dict()
        for path in paths:
            json, _ = get_json(path)
            result.update(json['instances'])
        return result
    
    def _save(self, old: dict, new: dict, name: str) -> None:
        ret = subtract_dicts(old[name], new[name])
        ret['timestamp'] = datetime.now()

        dir_name = self._collector.dir_name
        if dir_name:
            dir_name = join_path(dir_name, name.split("_")[0])

        save_csv(ret, name, dir_name=dir_name)

    def _collect(self, paths: List[str]) -> None:
        old = self._collect_per_path(paths)

        sleep(COLLECT_INTERVAL)
        
        new = self._collect_per_path(paths)
        
        for monitor_name in in_both(old, new):
            self._save(old, new, monitor_name)
        
        self._log.info(f'Saved data of monitor {self}')

    def _check_paths(self, url: str) -> dict:
        if not self.paths:
            self.paths = self._collector._get_paths(url)

    def run(self) -> None:
        name = self._monitor_name
        addr = self._addr
        self._log.info(f"Starting MonitorHandler for {name}@{addr}")
        monitor_url = f'http://{self._addr}'
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
            sockfd.connect((self._collector.address, self._collector.port))

            self._check_paths(monitor_url)

            send_to(sockfd, f'{name}@{addr}')

            while True:
                msg, _ = receive(sockfd)
                self._log.info('Received message: %s' % msg)

                if msg == START_MESSAGE:
                    self._log.info(f'Started collecting data from {name}@{addr}')

                    while not self._collector.stop_request:
                            
                        if not self._collector.stop_request:
                            self._collector.loop_barrier.wait()

                        self._collect(self.paths)

                        if self._collector.stop_request:
                            self._log.info('Releasing the barrier.')
                            self._collector.barrier.release()
