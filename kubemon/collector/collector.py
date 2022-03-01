from kubemon.collector.commands import COMMAND_CLASSES, HelpCommand
from kubemon.collector.monitor_handler import MonitorHandler
from kubemon.log import create_logger

from kubemon.settings import ( 
    CLI_PORT,
    COLLECTOR_HEALTH_CHECK_PORT,
    MONITOR_PORT,
    SERVICE_NAME
)
from kubemon.utils.data import (
    diff_list, in_both, save_csv, subtract_dicts
)
from kubemon.utils.networking import nslookup, receive, send_to, _check_service

from typing import Dict
from time import sleep
from os.path import join as join_path
from datetime import datetime

import socket
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
        self.name = self.__class__.__name__
        self.__running_since = None
        self.__daemons = dict()
        self.collector_sockets = dict()
        self.collect_status = dict()
        self.event = threading.Event()
        self.stop_request = False
        self.logger = LOGGER
        self.metric_paths = list()
        self._monitor_threads = list()

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
        return len(self.collector_sockets)

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

        self._handle_monitors()

    def __probe_for_daemons(self) -> None:
        if not _check_service(SERVICE_NAME):
            raise EnvironmentError(f'Missing \'{SERVICE_NAME}\' env. var')

        old_services = nslookup(SERVICE_NAME, MONITOR_PORT)
        while True:
            sleep(3)
            new_services = nslookup(SERVICE_NAME, MONITOR_PORT)

            if old_services != new_services:
                diff_services = diff_list(old_services, new_services)

                for service in diff_services:
                    resp = requests.get(f'http://{service}:{MONITOR_PORT}/').json()

                    with self.mutex:
                        self.__daemons[resp['hostname']] = service

            old_services = new_services

    def __is_alive(self) -> None:
        with self.setsock(self.address, COLLECTOR_HEALTH_CHECK_PORT, socket.SOCK_STREAM) as sockfd:
            sockfd.listen(2)

            while True:
                conn, _ = sockfd.accept()

                sleep(1)

                conn.close()

    def _handle_monitors(self) -> None:
        while True:
            with self.mutex:
                for hostname in self.__daemons:
                    addr = self.__daemons[hostname]
                    if hostname not in self._monitor_threads:
                        self.logger.info(f'Creating MonitorHandler for {hostname}@{addr}')
                        MonitorHandler(addr, hostname, self).start()
                        self._monitor_threads.append(hostname)
            sleep(3)
