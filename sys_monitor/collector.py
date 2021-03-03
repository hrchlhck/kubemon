from .constants import START_MESSAGE
from .utils import save_csv, receive, send_to
from addict import Dict
from datetime import datetime
import socket
import threading
import pickle
import sys


def start_thread(func, args):
    """
    Function to create and start a thread

        Args:
            func (function): Target function
            args (tuple): Target function arguments
    """
    threading.Thread(target=func, args=args).start()


class Collector(object):
    def __init__(self, address: str, port: int, instances: int):
        self.__address = address
        self.__port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind((self.__address, self.__port))
        self.__instances = instances
        self.__current_instances = 0
        self.__clients = list()
        self.__mutex = threading.Lock()
        print("Started collector at {}:{} waiting for {} monitors".format(
            self.__address, self.__port, self.__instances))

    def __accept_connections(self):
        clients = []
        while True:
            client, address = self.__socket.accept()
            print("\t + {}:{} connected".format(*address))

            start_thread(self.__listen_to_client, (client, address))
            clients.append(client)

            self.__mutex.acquire()
            try:
                self.__clients.append(client)
                self.__current_instances += 1
            finally:
                self.__mutex.release()

            print("\t Current monitors connected: {}".format(
                self.__current_instances))

            if self.__current_instances == self.__instances:
                self.start_clients(clients)
                clients = []

    def start_clients(self, clients):
        for client in clients:
            send_to(client, START_MESSAGE)
        print("Started")

    def start(self):
        self.__socket.listen()
        self.__accept_connections()

    def __listen_to_client(self, client: socket.socket, address: tuple) -> None:
        print("Creating new thread for client {}:{}".format(*address))

        while True:
            try:
                data = receive(client)

                if isinstance(data, dict):
                    data = Dict(data)

                print("Received {} from {}:{}".format(data.data, *address))
                send_to(client, "OK - {}".format(datetime.now()))
                file_name = "%s_%s_%s" % (
                    data.source, address[0].replace(".", "_"), address[1])
                save_csv(data.data, file_name,
                        dir_name=data.source.split('_')[0])
            except (ConnectionAbortedError, ConnectionResetError, EOFError) as e:
                if client in self.__clients:
                    self.__mutex.acquire()
                    try:
                        self.__clients.remove(client)
                        self.__current_instances -= 1
                    finally:
                        self.__mutex.release()
                print("Socket %s has died because %s" % (client, e))
                exit(1)
