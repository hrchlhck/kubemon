from typing import List
from kubemon.collector.commands import COMMAND_CLASSES
from ..dataclasses import Client
from ..config import DATA_PATH, DEFAULT_CLI_PORT, DEFAULT_MONITOR_PORT
from ..utils import save_csv, receive, send_to
from addict import Dict
from datetime import datetime
from os.path import join as join_path
import socket
import threading
from ..log import create_logger

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

    @property
    def address(self):
        return self.__address

    @property
    def port(self):
        return self.__port
    
    @property
    def cli_port(self):
        return self.__cli_port
       
    @property
    def connected_instances(self):
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

    def __accept_connections(self, sockfd: socket.socket) -> None:
        LOGGER.debug("Started function __accept_connections")
        while True:
            client, address = sockfd.accept()

            # Receiving the monitor name
            name, _ = receive(client)

            LOGGER.debug(f"Received name={name}")

            client = Client(name, client, client.getsockname())

            self.mutex.acquire()
            self.__instances.append(client)
            self.mutex.release()

            LOGGER.info(f"{name} connected. Address={address[0]}:{address[1]}")

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

            LOGGER.info(f"Received command '{data}' from {addr[0]}:{addr[1]}")

            if data:              
                cmd = data[0].lower() # Command

                if cmd == "start":
                    if len(data) == 2:
                        self.dir_name = data[1]
                        LOGGER.debug(f"dir_name setted to {self.dir_name}")
                    cmd_args = (self.__instances, self.dir_name, self.address)
                    self.is_running = True
                elif cmd == "instances":
                    cmd_args = (self.daemons,)
                elif cmd == "daemons":
                    cmd_args = (self.__instances,)
                elif cmd == "stop":
                    cmd_args = (self.__instances, self.daemons, self.is_running) 
                    self.is_running = False
                elif cmd == "help":
                    cmd_args = (COMMAND_CLASSES,)
                else:
                    cmd_args = tuple()

                command = COMMAND_CLASSES.get(cmd)

                if command == None:
                    command = COMMAND_CLASSES['not exist']

                command = command(*cmd_args)
                message = command.execute()

                send_to(cli, message, address=addr)
                LOGGER.debug(f"Sending '{message}' to {addr[0]}:{addr[1]}")

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
            LOGGER.error(f"Error while trying to bind socket to port {port}")
            sockfd.close()
            exit(1)
        return sockfd

    def __start_cli(self) -> None:
        """ Wrapper function to setup CLI. """
        
        # Setup socket
        with self.__setup_socket(self.address, self.cli_port, socket.SOCK_DGRAM) as sockfd:
            LOGGER.info(f'Started collector CLI at {self.address}:{self.cli_port}')

            # Start listening for commands
            self.__listen_cli(sockfd)

    def __start_collector(self) -> None:
        """ Wrapper function to setup the collector. """

        # Setup socket
        with self.__setup_socket(self.address, self.port, socket.SOCK_STREAM) as sockfd:
            sockfd.listen()
            LOGGER.info(f"Started collector at {self.address}:{self.port}")

            # Start accepting incoming connections from monitors
            self.__accept_connections(sockfd)
    
    def run(self) -> None:
        """ Start the collector """
        start_thread(self.__start_cli)
        self.__start_collector()
        LOGGER.debug("Call from function start")

    def __listen_monitors(self, client: Client) -> None:
        """ Listen for monitors. 

        Args:
            client (socket.socket): Monitor socket
            address (tuple): Monitor address
        
        Returns: None
        """
        LOGGER.info(f"Creating new thread for client {client.name}@{client.address[0]}:{client.address[1]}")

        while True:
            try:
                data, _ = receive(client.socket_obj)
                
                if data != None:
                    LOGGER.info(f"Successfully received data from {client.name}@{client.address[0]}:{client.address[1]}")
                else:
                    LOGGER.info(f"Received nothing from {client.name}")

                if isinstance(data, dict):
                    data = Dict(data)

                    data.data.update({'timestamp': datetime.now()})
                    
                    dir_name = data.source
                    if self.dir_name:
                        dir_name = join_path(self.dir_name, data.source.split("_")[0])
                    
                    save_csv(data.data, data.source, dir_name=dir_name)
                    LOGGER.debug(f"Saving data to {str(DATA_PATH)}/{self.dir_name}/{data.source}")

                msg = f"OK - {datetime.now()}"
                send_to(client.socket_obj, msg)
                LOGGER.debug(f"Sending '{msg}' to client {client.name}")

            except:
                addr, port = client.address
                LOGGER.info(f"Unregistered {client.name} {addr}:{port}")
                LOGGER.error('What happened??', exc_info=1)
                self.mutex.acquire()
                self.__instances.remove(client)
                self.mutex.release()

                # Killing thread
                exit(1)
