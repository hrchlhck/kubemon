from .constants import START_MESSAGE
from .utils import save_csv, receive, send_to
from addict import Dict
from datetime import datetime
from collections import deque
import socket
import threading
import sys


def start_thread(func, args=tuple()):
    """
    Function to create and start a thread

        Args:
            func (function): Target function
            args (tuple): Target function arguments
    """
    threading.Thread(target=func, args=args).start()


class Collector(object):
    def __init__(self, address: str, port: int, cli_port=9880):
        self.__address = address
        self.__port = port
        self.__cli_port = cli_port
        self.__mutex = threading.Lock()
        self.__instances = deque()

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
    def mutex(self):
        return self.__mutex
    
    @property
    def connected_instances(self):
        return len(self.__instances)

    def __accept_connections(self, sockfd: socket.socket) -> None:
        while True:
            client, address = sockfd.accept()

            self.mutex.acquire()
            self.__instances.append(client)
            self.mutex.release()

            print("\t[+] {}:{} connected".format(*address))

            start_thread(self.__listen_to_client, (client, address))
  
    def __listen_cli(self, client: socket.socket) -> None:
        while True:
            data, addr = receive(client)

            if data:
                print("\t[*] Command '{}' received from {}:{}".format(data, *addr))
                if data == "/start":
                    if self.connected_instances == 0:
                        message = f"There are no connected monitors to be started"
                    else:
                        message = f"Starting {self.connected_instances} monitors"
                        self.__start_instances()
                elif data == "/instances":
                    message = f"Connected instances: {self.connected_instances}"
                else:
                    message = "Command does not exist"

                send_to(client, message, address=addr)

    def __start_instances(self):
        for client in self.__instances:
            send_to(client, START_MESSAGE)
            print(f"Started client {client}")

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
            print(f"Error while trying to bind socket to port {port}")
            sockfd.close()
            exit(1)
        return sockfd

    def __start_cli(self):
        sockfd = self.__setup_socket(self.address, self.cli_port, socket.SOCK_DGRAM)
        print(f"Started collector CLI at {self.address}:{self.cli_port}")
        self.__listen_cli(sockfd)

    def __start_collector(self):
        sockfd = self.__setup_socket(self.address, self.port, socket.SOCK_STREAM)
        sockfd.listen()
        print(f"Started collector at {self.address}:{self.port}")
        self.__accept_connections(sockfd)
    
    def start(self):
        start_thread(self.__start_cli)
        start_thread(self.__start_collector)

    def __listen_to_client(self, client: socket.socket, address: tuple) -> None:
        print("Creating new thread for client {}:{}".format(*address))

        while True:
            try:
                data = receive(client, buffer_size=2048)

                print("Received {} from {}:{}".format(data, *address))

                if isinstance(data, dict):
                    data = Dict(data)
                    file_name = f"{data.source}_{address[0].replace('.', '_')}_{address[1]}"
                    save_csv(data.data, file_name, dir_name=data.source.split('_')[0])

                send_to(client, f"OK - {datetime.now()}")

            except (ConnectionAbortedError, ConnectionResetError, EOFError) as e:
                print(f"\t[-] {client} has died because {e}")
                self.mutex.acquire()
                self.__instances.remove(client)
                self.mutex.release()
                exit(1)
