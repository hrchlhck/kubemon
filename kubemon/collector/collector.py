from kubemon.collector.commands import COMMAND_CLASSES, HelpCommand
from kubemon.collector.monitor_handler import MonitorHandler
from kubemon.log import create_logger
from kubemon.utils.networking import nslookup, receive, send_to, get_json
from kubemon.settings import ( 
    CLI_PORT,
    COLLECTOR_HEALTH_CHECK_PORT,
    MONITOR_PORT,
    SERVICE_NAME,
    Volatile
)

from typing import Dict, List
from time import sleep
from datetime import datetime

import socket
import os
import threading
import requests

def start_thread(func, args=tuple()):
    """
    Function to create and start a thread

        Args:
            func (function): Target function
            args (tuple): Target function arguments
    """
    threading.Thread(target=func, args=args).start()

LOGGER = create_logger(__name__)

class Collector(threading.Thread):
    def __init__(self, address: str, port: int, cli_port=CLI_PORT):
        threading.Thread.__init__(self)
        self.__address = address
        self.__port = port
        self.__cli_port = cli_port
        self.dir_name = None
        self.mutex = threading.Lock()
        self.__running_since = None
        self.__daemons = dict()
        self.barrier = threading.Semaphore(0)
        self.loop_barrier = threading.Barrier(Volatile.NUM_DAEMONS)
        self.stop_request = False
        self.is_running = False
        self.logger = LOGGER
        self.__metric_paths: List[str] = list()
        self._monitor_threads: List[str] = list()
        self._monitor_sockets: List[socket.socket] = list()
        self._alive = False

    @property
    def address(self) -> str:
        return self.__address

    @property
    def port(self) -> int:
        return self.__port
    
    @property
    def cli_port(self) -> int:
        return self.__cli_port
    
    @property
    def daemons(self) -> Dict[str, str]:
        return self.__daemons

    @property
    def running_since(self) -> str:
        return self.__running_since
    
    @running_since.setter
    def running_since(self, val: datetime) -> None:
        self.__running_since = val
 
    def __len__(self):
        return len(self._monitor_sockets)

    @property
    def metric_paths(self) -> List[str]:
        return self.__metric_paths

    def set_metric_paths(self, url: str) -> None:
        if not url.startswith('http://'):
            url = f'http://{url}'

        if not self.__metric_paths:
            resp = requests.get(url).json()

            with self.mutex:
                self.__metric_paths = resp['metric_paths']
                self.logger.info(f'Set metric paths to {self.metric_paths}')

    def _get_paths(self, url: str) -> str:
        self.set_metric_paths(url)

        return [url + p for p in self.metric_paths]

    def __listen_cli(self, cli: socket.socket) -> None:
        """ 
        Function to receive and redirect commands from a CLI to monitors. 
        Currently it is based on UDP sockets.

        Args:
            cli (socket.socket): client socket
        
        Returns:
            None
        """
        while True:
            self.logger.info(f'CLI waiting for connections')

            conn, addr = cli.accept()
            self.logger.info(f'CLI accepted connection with {addr[0]}:{addr[1]}')

            while True:
                self.logger.info('Waiting for commands')

                data, _ = receive(conn)

                # Splitting from 'command args' -> [command, args]
                data = data.split()

                self.logger.info(f"Received command '{data}' from {addr[0]}:{addr[1]}")

                message = ""
                if data:              
                    cmd = data[0].lower() # Command                      

                    command = COMMAND_CLASSES.get(cmd)

                    if not command:
                        command = COMMAND_CLASSES['not exist']

                    command = command(self)

                    if cmd == 'help':
                        command = HelpCommand(COMMAND_CLASSES)
                    elif cmd == 'start':
                        if len(data) >= 2:
                            self.dir_name = data[1]
                            self.logger.debug(f"dir_name set to {self.dir_name}")

                    message = command.execute()

                send_to(conn, message)

                self.logger.debug(f"Sending '{message}' to {addr[0]}:{addr[1]}")

                if cmd == 'exit':
                    break

    def setsock(self, address: str, port: int, socktype: socket.SocketKind) -> socket.socket:
        """ 
        Setup a server socket 
        
        Args:
            address (str): Address for binding
            port (int):    Port for binding
        """
        sockfd = socket.socket(socket.AF_INET, socktype)
        try:
            sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sockfd.bind((address, port))
        except Exception as e:
            self.logger.error(f"Error while trying to bind socket to port {port}. {e}")
            sockfd.close()
            exit(1)
        return sockfd

    def __start_cli(self) -> None:
        """ Wrapper function to setup CLI. """
        
        # Setup socket
        with self.setsock(self.address, self.cli_port, socket.SOCK_STREAM) as sockfd:
            self.logger.info(f'Started collector CLI at {self.address}:{self.cli_port}')
            sockfd.listen(3)

            # Start listening for commands
            self.__listen_cli(sockfd)

    def run(self) -> None:
        """ Start the collector """
        start_thread(self.__start_cli)
        start_thread(self.__is_alive)
        start_thread(self.__probe_for_daemons)

        self._listen_monitor_handler()

    def _check_new_services(self, new_svc: List[str]) -> List[str]:
        if not new_svc:
            return []

        current_daemons = list(self.__daemons.values())
        return set(new_svc) - set(current_daemons)

    def __probe_for_daemons(self) -> None:
        self._wait_alive()

        while True:
            sleep(1)
            services = nslookup(SERVICE_NAME, MONITOR_PORT)

            new_services = self._check_new_services(services)
            if not new_services:
                continue

            for service in new_services:
                url = f'http://{service}:{MONITOR_PORT}'

                json, status_code = get_json(url)

                if status_code != 200:
                    self.logger.info(f'Monitor {service} could not be registered.')
                    self.logger.info(f'Status code: {status_code}')
                    continue

                host_str = f'{json["hostname"]}@{service}:{MONITOR_PORT}'
                
                status = self._add_monitor(f'{service}:{MONITOR_PORT}', json['hostname'])

                if status:
                    self.logger.info(f'Registered monitor {host_str}')
                    
                    self.set_metric_paths(url)

                    with self.mutex:
                        self.__daemons[json['hostname']] = service



    def __is_alive(self) -> None:
        with self.setsock(self.address, COLLECTOR_HEALTH_CHECK_PORT, socket.SOCK_STREAM) as sockfd:
            sockfd.listen(2)

            while True:
                conn, _ = sockfd.accept()

                conn.close()

    def _wait_alive(self):
        while not self._alive:
            sleep(2)
        self.logger.info('I\'m alive')

    def _add_monitor(self, address: str, hostname: str) -> bool:
        if hostname not in self._monitor_threads:
            mh = MonitorHandler(address, hostname, self)

            mh.start()

            with self.mutex:
                self._monitor_threads.append(hostname)
            
            return True
        return False
    
    def _listen_monitor_handler(self) -> None:
        with self.setsock(self.address, self.port, socket.SOCK_STREAM) as sockfd:
            sockfd.listen()

            self._alive = True

            while True:
                conn, _ = sockfd.accept()
                
                hostname, _ = receive(conn)

                self.logger.info(f'Connection stablished between collector and {hostname}')

                self._monitor_sockets.append(conn)
