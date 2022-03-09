from kubemon.collector.commands import IsAliveCommand, COMMAND_CLASSES
from kubemon.utils.networking import receive, send_to, is_alive
from kubemon.settings import COLLECTOR_HEALTH_CHECK_PORT

from typing import Any
from time import sleep

import socket

__all__ = ["CollectorClient"]

def _check_alive(address: str, port: int) -> None:
    print('Waiting for collector to be alive')
    while not is_alive(address, port):
        sleep(1)
    else:
        print('Collector is alive!')

class ExecCommand:
    def __init__(self, address: str, port: int, cmd: str):
        self.__cmd = cmd
        self.__address = address
        self.__port = port

    @property
    def cmd(self) -> str:
        return self.__cmd
    
    @property
    def address(self):
        return self.__address
    
    @property
    def port(self):
        return self.__port
    
    def exec(self, *args) -> Any:
        if self.cmd == 'alive':
            data = IsAliveCommand(self.address, COLLECTOR_HEALTH_CHECK_PORT).execute()
            return data
        
        composed_cmd = self.cmd + " " + " ".join(map(str, args))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sockfd:
            sockfd.connect((self.address, self.port))

            send_to(sockfd, composed_cmd)
            data, _ = receive(sockfd)
            print(data)

            send_to(sockfd, 'exit')
            _, _ = receive(sockfd)
            
            return data

class CollectorClient:
    def __init__(self, address: str, port: int):
        self.__address = address
        self.__port = port

        for k in COMMAND_CLASSES:
            setattr(self, k, ExecCommand(address, port, k).exec)
    
    @property
    def address(self):
        return self.__address
    
    @property
    def port(self):
        return self.__port

    def run(self) -> None:
        _check_alive(self.address, COLLECTOR_HEALTH_CHECK_PORT)

        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd.connect((self.address, self.port))

        try:
            cmd = ""
            while cmd != "exit":
                cmd = input(">>> ")
                
                if cmd == "alive":
                    data = IsAliveCommand(self.address, COLLECTOR_HEALTH_CHECK_PORT).execute()
                    print(data)
                    continue

                send_to(sockfd, cmd)

                data, _ = receive(sockfd)
                print(data)
        except KeyboardInterrupt:
            send_to(sockfd, 'exit')
            data, _ = receive(sockfd)
            print(data)
        finally:
            sockfd.close()
