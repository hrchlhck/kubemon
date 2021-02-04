from functools import reduce
from os.path import join, isfile
from pathlib import Path
from typing import List, Tuple
from requests import get
from operator import sub
import socket
import csv
import sys

### Constants ###
CONNECTION_DIED_CODE = "#!"

### Functions ###
def subtract_dicts(dict1: dict, dict2: dict) -> dict:
    """ Subtracts values from dict1 and dict2 """
    if len(dict1) != len(dict2):
        raise KeyError("Mapping key not found")
    values = map(lambda _dict: reduce(sub, _dict),
                 zip(dict2.values(), dict1.values()))
    return dict(zip(dict1.keys(), map(lambda n: round(n, 4), values)))


def merge_dict(*dicts: List[dict]) -> dict:
    """ Merges multiple dictionaries """
    result = {}
    for d in dicts:
        if d != None:
            result.update(d)
    return result


def filter_dict(_dict: dict, *keys: List[object]) -> dict:
    """ Apply a simple filter over a given dictionary
        Usage:
            >>> filter_dict({'a': 1, 'b': 2, 'c':3}, 'a', 'c')
            >>> {'a': 1, 'c': 3}
    """
    filters = keys
    if isinstance(keys[0], list):
        filters = keys[0]
    return {k: v for k, v in _dict.items() if k in filters}


def join_url(url: str, *pages: List[str]) -> str:
    """ Joins pages in a given URL. 
        Usage:
            >>> join('https://github.com', 'hrchlhck', 'sys-monitor')
            >>> 'https://github.com/hrchlhck/sys-monitor'
    """
    for page in map(str, pages):
        url += "/" + page
    return url


def load_json(url: str) -> dict:
    """ Parses a JSON to a Python dictionary """
    try:
        return get(url).json()
    except Exception as e:
        print(e)


def send_data(socket: socket.socket, data: dict, source: str) -> None:
    """ 
    This function is responsible for sending data via network socket
    to a TCP Server inside of sys_monitor/collector.py.

    Arguments:
        data -> A dictionary containing your data
        source -> From where you are sending the data
        socket -> TCP socket

    Usage:
        >>> send_data(('localhost', 9999), {'cpu_usage': 120, 'memory': 0.5}, 'sys_monitor')
        >>> # Response from server
        >>> OK - 2020-11-04 14:07:31.339432
    """
    size = 1024
    temp = f"('{source}', {data})"
    socket.send(temp.encode("utf-8"))
    print(socket.recv(size).decode("utf-8"))


def save_csv(_dict, name, dir_name=sys.argv[-1]):
    """ Saves a dict into a csv """

    filename = f"{name}.csv"
    _dir = join("data", dir_name)

    Path(_dir).mkdir(parents=True, exist_ok=True)

    _dir = join(_dir, filename)

    mode = "a"

    if not isfile(_dir):
        mode = "w"

    with open(_dir, mode=mode, newline="") as f:
        writer = csv.DictWriter(f, _dict.keys())

        if mode == "w":
            writer.writeheader()

        writer.writerow(_dict)
