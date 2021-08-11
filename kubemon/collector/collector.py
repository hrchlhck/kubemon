from kubemon.collector.commands import ConnectedMonitorsCommand, InstancesCommand, NotExistCommand, StartCommand
from ..dataclasses import Client
from ..config import DEFAULT_CLI_PORT
from ..utils import save_csv, receive, send_to
from addict import Dict
from datetime import datetime
from sty import fg
from os.path import join as join_path
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


class Collector(object):
    def __init__(self, address: str, port: int, cli_port=DEFAULT_CLI_PORT):
        self.__address = address
        self.__port = port
        self.__cli_port = cli_port
        self.__mutex = threading.Lock()
        self.__instances = list()
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

            # Receiving the monitor name
            name, _ = receive(client, buffer_size=512)
            client = Client(name, client, client.getsockname())

            self.mutex.acquire()
            self.__instances.append(client)
            self.mutex.release()

            print("\t[ {}+{} ] {}@{}:{} connected".format(fg(0, 255, 0), fg.rs, name, *address), flush=True)

            start_thread(self.__listen_monitors, (client,))
  
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

            print("\t[ {}*{} ] Command '{}' received from {}:{}".format(fg(0, 90, 255), fg.rs, data, *addr), flush=True)

            if data:                
                cmd = data[0] # Command

                if cmd == "/start":
                    if len(data) == 2:
                        self.dir_name = data[1]
                    command = StartCommand(self.__instances, self.dir_name, self.address)
                elif cmd == "/instances":
                    command = InstancesCommand(self.__instances)
                elif cmd == "/monitors":
                    command = ConnectedMonitorsCommand(self.__instances)
                else:
                    command = NotExistCommand()           

                message = command.execute()
                send_to(cli, message, address=addr)

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

    def __start_cli(self) -> None:
        """ Wrapper function to setup CLI. """
        
        # Setup socket
        sockfd = self.__setup_socket(self.address, self.cli_port, socket.SOCK_DGRAM)
        print(f"{self.__tag}Started collector CLI at {self.address}:{self.cli_port}", flush=True)

        # Start listening for commands
        self.__listen_cli(sockfd)

    def __start_collector(self) -> None:
        """ Wrapper function to setup the collector. """

        # Setup socket
        sockfd = self.__setup_socket(self.address, self.port, socket.SOCK_STREAM)
        sockfd.listen()
        print(f"{self.__tag}Started collector at {self.address}:{self.port}", flush=True)

        # Start accepting incoming connections from monitors
        self.__accept_connections(sockfd)
    
    def start(self) -> None:
        """ Start the collector """
        start_thread(self.__start_cli)
        start_thread(self.__start_collector)

    def __listen_monitors(self, client: Client) -> None:
        """ Listen for monitors. 

        Args:
            client (socket.socket): Monitor socket
            address (tuple): Monitor address
        
        Returns: None
        """
        print("{}Creating new thread for client {}@{}:{}".format(self.__tag, client.name, *client.address), flush=True)

        while True:
            try:
                data, _ = receive(client.socket_obj, buffer_size=2048)

                if data != None:
                    print(f"{self.__tag}Successfully received data from {client.name}@{client.address[0]}:{client.address[1]}", flush=True)
                else:
                    print(f"{self.__tag}Received nothing from ")

                if isinstance(data, dict):
                    data = Dict(data)

                    data.data.update({'timestamp': datetime.now()})
                    
                    dir_name = data.source
                    if self.dir_name:
                        dir_name = join_path(self.dir_name, data.source.split("_")[0])
                    
                    save_csv(data.data, data.source, dir_name=dir_name)

                send_to(client.socket_obj, f"OK - {datetime.now()}")

            except:
                addr, port = client.address
                print(f"\t[ {fg(255, 0, 0)}- {fg.rs}] Unregistered {client.name} {addr}:{port}", flush=True)
                self.mutex.acquire()
                self.__instances.remove(client)
                self.mutex.release()

                # Killing thread
                exit(1)
