from http.server import BaseHTTPRequestHandler, HTTPServer
from os.path import join, isfile, isdir
from os import getcwd, makedirs, listdir
import json
import csv


def create_dir(_dir):
    if not isdir(_dir):
        makedirs(_dir)
    return _dir


def save_csv(_dict, name):
    """ Saves a dict into a csv """

    filename = f"{name}{len(listdir('data'))}".replace(".", "_") + ".csv"
    _dir = join(create_dir("data"), filename)

    mode = "a"

    if not isfile(_dir):
        mode = "w"

    with open(_dir, mode=mode, newline="") as f:
        writer = csv.DictWriter(f, _dict.keys())

        if mode == "w":
            writer.writeheader()

        writer.writerow(_dict)


class HTTPHandler(BaseHTTPRequestHandler):
    def __set_response(self, val="POST"):
        _val = "application/json" if val == "POST" else "text/html"
        self.send_response(200)
        self.send_header("Content-type", _val)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        _from = self.headers["from"]
        post_data = self.rfile.read(content_length).decode("utf-8")
        json_to_dict = json.loads(json.loads(post_data))
        print(json_to_dict)
        save_csv(json_to_dict, _from)

        self.__set_response()
        self.wfile.write("POST request for {}\n".format(self.path).encode("utf-8"))

        del post_data, json_to_dict

    def do_GET(self):
        self.__set_response("GET")
        with open("static/index.html", "rb") as f:
            self.wfile.write(f.read())


class Collector:
    def __init__(self, addr, port):
        self.__port = port
        self.__addr = addr

    def start(self, server_class=HTTPServer, handler_class=HTTPHandler):
        server_address = (self.__addr, self.__port)
        httpd = server_class(server_address, handler_class)
        print("Serving at port:", self.__port)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
