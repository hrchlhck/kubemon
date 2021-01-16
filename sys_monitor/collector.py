from .utils import save_csv, CONNECTION_DIED_CODE
from datetime import datetime
import socketserver, socket
from socket import timeout as TimeoutException
import threading


class Collector(object):
    def __init__(self, host: str, port: int, instances: int):
        self.__host = host
        self.__port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind((self.__host, self.__port))
        self.__instances = instances
        print("Started collector at {}:{}".format(self.__host, self.__port))

    def start(self):
        self.__socket.listen()
        clients = []
        threads = []
        current_instances = 0

        while current_instances != self.__instances:
            client, address = self.__socket.accept()
            print("\t + {}:{} connected".format(*address))
            threads.append(threading.Thread(target=self.__listen_to_client, args=(client, address)))
            clients.append(client)
            current_instances += 1
            print("\t Current monitors connected: {}".format(current_instances))

        line = input(">>> ")

        while line != "start" or line != "exit":
            if line == "start":
                for _client in clients:
                    _client.sendall("start".encode('utf8'))
                
                for thread in threads:
                    if not thread.is_alive():
                        thread.start()
                break
            elif line == "exit":
                exit(1)

                
    def __listen_to_client(self, client: socket.socket, address: tuple) -> None:
        size = 1024
        
        print("Creating new thread for client {}:{}".format(*address))
        
        while True:
            try:
                data = client.recv(size).decode("utf-8")
                if data and CONNECTION_DIED_CODE not in data:
                    data = eval(data)
                    save_csv(data[1], data[0] + "_" + address[0].replace(".", "_"))
                    print("Received {} from {}:{}".format(data[1], *address))
                    client.sendall("OK - {}".format(datetime.now()).encode('utf-8'))
                elif CONNECTION_DIED_CODE in data:
                    print("Client {} died".format(client.getpeername()))
                    break
            except TimeoutException as e:
                print(e)
                print("Client {} died".format(client.getpeername()))
                
                