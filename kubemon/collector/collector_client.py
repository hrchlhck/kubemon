from ..utils import receive, send_to
import socket
import sys

__all__ = ["CollectorClient"]

class CollectorClient(object):
    def __init__(self, address: str, port: int):
        self.__address = address
        self.__port = port
    
    @property
    def address(self):
        return self.__address
    
    @property
    def port(self):
        return self.__port

    def exec(self, cmd):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            send_to(sockfd, cmd, (self.address, self.port))
            data, addr = receive(sockfd)
            print(data)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            cmd = ""
            while cmd != "exit":
                cmd = input(">>> ")
                
                if cmd == "exit":
                    print("Exiting CLI")
                    sys.exit(1)

                send_to(sockfd, cmd, (self.address, self.port))

                data, addr = receive(sockfd)
                print(data)
