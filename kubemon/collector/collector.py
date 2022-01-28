from kubemon.collector.commands import COMMAND_CLASSES, HelpCommand
from kubemon.dataclasses import Client
from kubemon.log import create_logger

from kubemon.config import (
    DATA_PATH, DEFAULT_CLI_PORT,
    DEFAULT_MONITOR_PORT, 
    COLLECTOR_HEALTH_CHECK_PORT
)
from kubemon.utils import (
    save_csv, receive, send_to
)

from typing import List
from time import sleep
from os.path import join as join_path
from addict import Dict
from datetime import datetime

import socket
import threading

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
    def __init__(self, address: str, port: int, cli_port=DEFAULT_CLI_PORT):
        threading.Thread.__init__(self)
        self.__address = address
        self.__port = port
        self.__cli_port = cli_port
        self.__instances = list()
        self.dir_name = None
        self.is_running = False
        self.name = self.__class__.__name__
        self.mutex = threading.Lock()
        self.__running_since = None
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
    def instances(self) -> List[Client]:
        return self.__instances
    
    @instances.setter
    def instances(self, val: list) -> None:
        self.__instances = val

    @property
    def connected_instances(self) -> int:
        return len(self.__instances)
    
    @property
    def daemons(self) -> List[str]:
        get_raddr = lambda x: x.socket_obj.getsockname()[0] if x.socket_obj.getsockname()[1] != DEFAULT_MONITOR_PORT else x.socket_obj.getpeername()
        unique = []

        for client in self.__instances:
            addr = get_raddr(client)
            if addr[0] not in unique:
                unique.append(addr[0])

        return unique

    @property
    def running_since(self) -> str:
        return self.__running_since
    
    @running_since.setter
    def running_since(self, val: datetime) -> None:
        self.__running_since = val

    def __accept_connections(self, sockfd: socket.socket) -> None:
        self.logger.debug("Started function __accept_connections")
        while True:
            client, address = sockfd.accept()

            # Receiving the monitor name
            name, _ = receive(client)

            self.logger.debug(f"Received name={name}")

            client = Client(name, client, client.getsockname())

            self.mutex.acquire()
            self.__instances.append(client)
            self.mutex.release()

            self.logger.info(f"{name} connected. Address={address[0]}:{address[1]}")

            start_thread(self.__listen_monitors, (client,))

            print(self.daemons)
  
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
            data, addr = receive(cli)

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

            send_to(cli, message, address=addr)

            self.logger.debug(f"Sending '{message}' to {addr[0]}:{addr[1]}")

    def __setup_socket(self, address: str, port: int, socktype: socket.SocketKind) -> socket.socket:
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
        with self.__setup_socket(self.address, self.cli_port, socket.SOCK_DGRAM) as sockfd:
            self.logger.info(f'Started collector CLI at {self.address}:{self.cli_port}')

            # Start listening for commands
            self.__listen_cli(sockfd)

    def __start_collector(self) -> None:
        """ Wrapper function to setup the collector. """

        # Setup socket
        with self.__setup_socket(self.address, self.port, socket.SOCK_STREAM) as sockfd:
            sockfd.listen()
            self.logger.info(f"Started collector at {self.address}:{self.port}")

            # Start accepting incoming connections from monitors
            self.__accept_connections(sockfd)
    
    def run(self) -> None:
        """ Start the collector """
        start_thread(self.__start_cli)
        start_thread(self.__is_alive)
        self.__start_collector()
        self.logger.debug("Call from function start")

    def __is_alive(self) -> None:
        with self.__setup_socket(self.address, COLLECTOR_HEALTH_CHECK_PORT, socket.SOCK_STREAM) as sockfd:
            sockfd.listen(2)

            while True:
                conn, _ = sockfd.accept()

                sleep(1)

                conn.close()

    def __listen_monitors(self, client: Client) -> None:
        """ Listen for monitors. 

        Args:
            client (socket.socket): Monitor socket
            address (tuple): Monitor address
        
        Returns: None
        """
        self.logger.info(f"Creating new thread for client {client.name}@{client.address[0]}:{client.address[1]}")

        while True:
            try:
                data, _ = receive(client.socket_obj)
                
                if data != None:
                    self.logger.info(f"Successfully received data from {client.name}@{client.address[0]}:{client.address[1]}")
                else:
                    self.logger.info(f"Received nothing from {client.name}")

                if isinstance(data, dict):
                    data = Dict(data)

                    data.data.update({'timestamp': datetime.now()})
                    
                    dir_name = data.source
                    if self.dir_name:
                        dir_name = join_path(self.dir_name, data.source.split("_")[0])
                    
                    save_csv(data.data, data.source, dir_name=dir_name)
                    self.logger.debug(f"Saving data to {str(DATA_PATH)}/{self.dir_name}/{data.source}")

                msg = f"OK - {datetime.now()}"
                send_to(client.socket_obj, msg)
                self.logger.debug(f"Sending '{msg}' to client {client.name}")

            except:
                addr, port = client.address
                self.logger.info(f"Unregistered {client.name} {addr}:{port}")
                self.logger.error('What happened??', exc_info=1)
                self.mutex.acquire()
                self.__instances.remove(client)
                self.mutex.release()

                # Killing thread
                exit(1)
