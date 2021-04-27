from ..constants import START_MESSAGE
from ..utils import save_csv, receive, send_to
from addict import Dict
from datetime import datetime
from collections import deque, namedtuple
from sty import fg, rs, ef
from os.path import join as join_path
import socket
import traceback
import threading
import sys

# Namedtuple to represent a socket client returned by socket.accept()
Client = namedtuple('Client', ['socket_object', 'address'])

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
        self.__tag = f"[ {fg(255, 200, 100)}{self.__class__.__name__}{fg.rs} ] "
        self.dir_name = None

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

            print("\t[ {}+{} ] {}:{} connected".format(fg(0, 255, 0), fg.rs, *address), flush=True)

            start_thread(self.__listen_to_client, (client, address))
  
    def __listen_cli(self, client: socket.socket) -> None:
        while True:
            data, addr = receive(client)

            print("\t[ {}*{} ] Command '{}' received from {}:{}".format(fg(0, 90, 255), fg.rs, data, *addr), flush=True)
            if data:                
                cmd = data[0] # Command

                if cmd == "/start":
                    if len(data) == 2:
                        self.dir_name = data[1]
                    if self.connected_instances == 0:
                        message = f"There are no connected monitors to be started"
                    else:
                        message = f"Starting {self.connected_instances} monitors"
                        self.__start_instances()
                elif cmd == "/instances":
                    message = f"Connected instances: {self.connected_instances}"
                else:
                    message = "Command does not exist"

                send_to(client, message, address=addr)

    def __start_instances(self):
        for client in self.__instances:
            send_to(client, START_MESSAGE)
            print(f"{self.__tag}Started client {client}", flush=True)

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
            print(f"{self.__tag}Error while trying to bind socket to port {port}", flush=True)
            sockfd.close()
            exit(1)
        return sockfd

    def __start_cli(self):
        sockfd = self.__setup_socket(self.address, self.cli_port, socket.SOCK_DGRAM)
        print(f"{self.__tag}Started collector CLI at {self.address}:{self.cli_port}", flush=True)
        self.__listen_cli(sockfd)

    def __start_collector(self):
        sockfd = self.__setup_socket(self.address, self.port, socket.SOCK_STREAM)
        sockfd.listen()
        print(f"{self.__tag}Started collector at {self.address}:{self.port}", flush=True)
        self.__accept_connections(sockfd)
    
    def start(self):
        start_thread(self.__start_cli)
        start_thread(self.__start_collector)

    def __listen_to_client(self, client: socket.socket, address: tuple) -> None:
        print("{}Creating new thread for client {}:{}".format(self.__tag, *address), flush=True)

        _client = Client(client, client.getsockname())

        while True:
            try:
                data, _ = receive(client, buffer_size=2048)

                print("{}Received {} from {}:{}".format(self.__tag, data, *address), flush=True)

                if isinstance(data, dict):
                    data = Dict(data)
                    
                    dir_name = data.source
                    if self.dir_name:
                        dir_name = join_path(self.dir_name, data.source.split("_")[0])
                    
                    save_csv(data.data, data.source, dir_name=dir_name)

                send_to(client, f"OK - {datetime.now()}")

            except:
                traceback.print_exc()
                addr, port = _client.address
                print(f"\t[ {fg(255, 0, 0)}- {fg.rs}] {addr}:{port}", flush=True)
                self.mutex.acquire()
                self.__instances.remove(client)
                self.mutex.release()
                exit(1)
