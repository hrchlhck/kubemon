from kubemon.collector.commands import COMMAND_CLASSES, HelpCommand
from kubemon.log import create_logger

from kubemon.config import ( 
    DATA_PATH, 
    START_MESSAGE,
    CLI_PORT,
    COLLECT_INTERVAL,
    COLLECT_TASK_PORT,
    COLLECTOR_HEALTH_CHECK_PORT,
    COLLECTOR_INSTANCES_CHECK_PORT,
    MONITOR_PORT
)
from kubemon.utils import (
    in_both, save_csv, receive, send_to, subtract_dicts
)

from typing import Dict as Dict_t, Tuple
from time import sleep
from os.path import join as join_path
from addict import Dict
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
    def daemons(self) -> Dict_t[str, str]:
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
        except:
            self.logger.error(f"Error while trying to bind socket to port {port}")
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
        start_thread(self.__register_daemons)

        self.listen_collect_task()

    def __register_daemons(self) -> None:
        with self.setsock(self.address, COLLECTOR_INSTANCES_CHECK_PORT, socket.SOCK_STREAM) as sockfd:
            sockfd.listen()
            self.logger.debug(f'Started thread for __register_daemons')

            while True:
                conn, addr = sockfd.accept()
                self.logger.debug(f'Accepted connection for {":".join(map(str, addr))}')
                start_thread(self.__listen_daemon, args=(conn,))

    def __is_alive(self) -> None:
        with self.setsock(self.address, COLLECTOR_HEALTH_CHECK_PORT, socket.SOCK_STREAM) as sockfd:
            sockfd.listen(2)

            while True:
                conn, _ = sockfd.accept()

                sleep(1)

                conn.close()

    def __listen_daemon(self, sockfd: socket.socket) -> None:
        self.logger.debug(f'Started thread for {":".join(map(str, sockfd.getsockname()))}')
        (name, addr), _ = receive(sockfd)

        self.logger.debug(f'Received name: {name}, and address {addr}')

        with self.mutex:
            self.__daemons[name] = addr

        self.collect_task(name, addr)

    def listen_collect_task(self) -> None:
        with self.setsock(self.address, COLLECT_TASK_PORT, socket.SOCK_STREAM) as sockfd:
            sockfd.listen()

            self.logger.info('Started listen_collect_task')
            while True:
                conn, addr = sockfd.accept()
                self.logger.info(f'Accepted connection at listen_collect_task for {addr}')

                msg, _ = receive(conn)
                self.logger.info(f'Received name {msg}')

                self.collector_sockets[msg] = conn
                
    def collect_task(self, name: str, addr: str) -> None:
        self.logger.info(f"Calling collect_task for {name}@{addr}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
            sockfd.connect((self.address, COLLECT_TASK_PORT))

            send_to(sockfd, name)

            while True:

                msg, _ = receive(sockfd)
                self.logger.info('Received message: %s' % msg)

                if msg == START_MESSAGE:
                    while not self.stop_request:
                        if self.stop_request:
                            self.logger.info(f'Stopped for {name}@{addr}')
                            break

                        old_data = requests.get(f'http://{addr}:{MONITOR_PORT}').json()

                        sleep(COLLECT_INTERVAL)
                        
                        new_data = requests.get(f'http://{addr}:{MONITOR_PORT}').json()

                        for k in in_both(old_data, new_data):
                            ret = subtract_dicts(old_data[k], new_data[k])
                            ret['timestamp'] = datetime.now()

                            if self.dir_name:
                                dir_name = join_path(self.dir_name, k.split("_")[0])

                            save_csv(ret, k, dir_name=dir_name)
                            self.logger.info(f"Saving data to {str(DATA_PATH)}/{self.dir_name}/{k}")

                            if self.stop_request:
                                self.event.set()


    def __listen_monitors(self, name: str, client: socket.socket, address: Tuple[str, int]) -> None:
        """ Listen for monitors. 

        Args:
            client (socket.socket): Monitor socket
        
        Returns: None
        """
        self.logger.info(f"Creating new thread for client {name}@{':'.join(map(str, address))}")

        while not self.stop_request:
            try:
                data, _ = receive(client)

                if data != None:
                    self.logger.info(f"Successfully received data from {name}@{':'.join(map(str, address))}")
                else:
                    self.logger.info(f"Received nothing from {name}")

                if isinstance(data, dict):
                    data = Dict(data)

                    data.data.update({'timestamp': datetime.now()})
                    
                    dir_name = data.source
                    if self.dir_name:
                        dir_name = join_path(self.dir_name, data.source.split("_")[0])
                    
                    save_csv(data.data, data.source, dir_name=dir_name)
                    self.logger.debug(f"Saving data to {str(DATA_PATH)}/{self.dir_name}/{data.source}")

                msg = f"OK - {datetime.now()}"
                send_to(client, msg)
                self.logger.debug(f"Sending '{msg}' to client {name}")

            except:
                addr, port = address
                self.logger.info(f"Unregistered {name} {addr}:{port}")
                self.logger.error('What happened??', exc_info=1)

                with self.mutex:
                    self.instances.pop(name)

                # Killing thread
                exit(1)
