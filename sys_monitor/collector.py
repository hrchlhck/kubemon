from .utils import save_csv
from datetime import datetime
import socketserver, socket
import threading


class TCPServer(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        print("From: {}".format(self.client_address[0]))
        data = eval(data.decode("utf-8"))
        print(data)
        save_csv(data[1], data[0] + "_" + self.client_address[0].replace(".", "_"))
        self.request.send("OK - {}".format(datetime.now()).encode("utf-8"))


class Collector(object):
    def __init__(self, host, port):
        self.__host = host
        self.__port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind((self.__host, self.__port))
        print("Started collector at {}:{}".format(self.__host, self.__port))

    def start(self):
        self.__socket.listen()
        while True:
            client, address = self.__socket.accept()
            threading.Thread(target=self.__listen_to_client, args=(client, address)).start()
                
    def __listen_to_client(self, client: socket.socket, address: tuple) -> None:
        size = 1024
        
        print("Creating new thread for client {}:{}".format(*address))
        
        while True:
            try:
                data = client.recv(size)
                client.settimeout(10)
                if data:
                    data = eval(data)
                    save_csv(data[1], data[0] + "_" + address[0].replace(".", "_"))
                    print("Received {} from \t {}:{}".format(data[1], *address))
                    client.sendall("OK - {}".format(datetime.now()).encode('utf-8'))
            except Exception as e:
                print(e)
                print("Client {} died".format(client.getpeername()))
                client.close()
                break
                
                