from .constants import CONNECTION_DIED_CODE
from .utils import save_csv, receive
from datetime import datetime
import socketserver
import socket
from socket import timeout as TimeoutException
from socket import gethostbyname
import threading
import pickle


class Collector(object):
    def __init__(self, host: str, port: int, instances: int):
        self.__host = host
        self.__port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind((self.__host, self.__port))
        self.__instances = instances
        self.__clients = list()
        self.__clients_hostnames = list()
        print("Started collector at {}:{}".format(self.__host, self.__port))

    def start(self):
        self.__socket.listen()
        threads = []
        current_instances = 0

        while current_instances != self.__instances:
            client, address = self.__socket.accept()
            print("\t + {}:{} connected".format(*address))
            threads.append(threading.Thread(
                target=self.__listen_to_client, args=(client, address)))
            self.__clients.append(client)
            self.__clients_hostnames.append(gethostbyname(address[0]))
            self.__clients_hostnames.append(client)
            current_instances += 1
            print("\t Current monitors connected: {}".format(current_instances))

        line = input(">>> ")

        while line != "start" or line != "exit":
            if line == "start":
                for _client in self.__clients:
                    _client.sendall("start".encode('utf8'))

                for thread in threads:
                    if not thread.is_alive():
                        thread.start()
                break
            elif line == "exit":
                exit(1)
            else:
                line = input(">>> ")

    def get_clients_hostnames(self):
        return tuple(self.__clients_hostnames)

    def __listen_to_client(self, client: socket.socket, address: tuple) -> None:
        print("Creating new thread for client {}:{}".format(*address))
        size = 1024

        while True:
            data = pickle.loads(client.recv(size), encoding="utf8")

            if not data:
                break
            elif data and 'data' in data and 'source' in data and data['data'] != CONNECTION_DIED_CODE:
                print("Received {} from {}:{}".format(data['data'], *address))
                client.sendall(
                    "OK - {}".format(datetime.now()).encode('utf-8'))
                file_name = "%s_%s_%s" % (
                    data['source'], address[0].replace(".", "_"), address[1])
                save_csv(data['data'], file_name,
                         dir_name=data['source'].split('_')[0])
            else:
                print("Client {} died".format(client.getpeername()))
                self.__clients.remove(client)
                break
