from .utils import save_csv
from datetime import datetime
import socketserver

class TCPServer(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        print("From: {}".format(self.client_address[0]))
        data = eval(data.decode("utf-8"))
        print(data)
        save_csv(data[1], data[0] + "_" + self.client_address[0].replace(".", "_"))
        self.request.send("OK - {}".format(datetime.now()).encode("utf-8"))


class Collector:
    def __init__(self, host, port):
        self.__host = host
        self.__port = port

    def start(self):
        with socketserver.TCPServer((self.__host, self.__port), TCPServer) as server:
            try:
                print("Serving started at address {}:{}".format(
                    self.__host, self.__port))
                server.serve_forever()
            except KeyboardInterrupt:
                print("Shutting down")
