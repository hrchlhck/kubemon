from ..utils import receive, send_to
import threading
import socket
import sys

__all__ = ["CollectorClient"]

class CollectorClient(threading.Thread):
    def __init__(self, address: str, port: int):
        self.__address = address
        self.__port = port
        threading.Thread.__init__(self)
    
    @property
    def address(self):
        return self.__address
    
    @property
    def port(self):
        return self.__port

    def exec(self, cmd):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            send_to(sockfd, cmd, (self.address, self.port))
            data, _ = receive(sockfd)
            print(data)
            return data

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sockfd:
            cmd = ""
            while cmd != "exit":
                cmd = input(">>> ")
                
                if cmd == "exit":
                    print("Exiting CLI")
                    sys.exit(1)

                send_to(sockfd, cmd, (self.address, self.port))

                data, _ = receive(sockfd)
                print(data)
