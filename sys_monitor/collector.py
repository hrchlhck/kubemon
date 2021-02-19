from .constants import CONNECTION_DIED_CODE
from .utils import save_csv, receive, send_to
from .decorators import wrap_exceptions
from addict import Dict
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

        for _client in self.__clients:
            send_to(_client, "start")

        for thread in threads:
            if not thread.is_alive():
                thread.start()

    @wrap_exceptions(KeyboardInterrupt, EOFError)
    def __listen_to_client(self, client: socket.socket, address: tuple) -> None:
        print("Creating new thread for client {}:{}".format(*address))

        while True:
            data = receive(client)

            if isinstance(data, dict):
                data = Dict(data)

            print("Received {} from {}:{}".format(data.data, *address))
            send_to(client, "OK - {}".format(datetime.now()))
            file_name = "%s_%s_%s" % (
                data.source, address[0].replace(".", "_"), address[1])
            save_csv(data.data, file_name,
                     dir_name=data.source.split('_')[0])
