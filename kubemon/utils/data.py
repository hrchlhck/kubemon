from kubemon.settings import DATA_PATH

from functools import reduce
from pathlib import Path
from os.path import join, isfile
from typing import Any, List

from csv import DictWriter

__all__ = ['subtract_dicts', 'merge_dict', 'filter_dict', 'in_both']

def subtract_dicts(dict1: dict, dict2: dict, operation=lambda x, y: x-y) -> dict:
    """ Subtracts values from dict1 and dict2 """
    if len(dict1) != len(dict2):
        raise KeyError("Mapping key not found")
    values = map(lambda _dict: reduce(operation, _dict),
                 zip(dict2.values(), dict1.values()))
    return dict(zip(dict1.keys(), map(lambda n: round(n, 4), values)))


def merge_dict(*dicts: List[dict]) -> dict:
    """ Merges multiple dictionaries """
    if not len(dicts):
        raise ValueError('Must specify dictionaries')
    
    if not all(i for i in dicts if isinstance(i, dict)):
        raise TypeError('All arguments specified must be \'dict\'')

    ret = dict()
    for d in dicts:
        ret.update(d)
    return ret


def filter_dict(_dict: dict, *keys: List[Any]) -> dict:
    """ Apply a simple filter over a given dictionary
        Usage:
            >>> filter_dict({'a': 1, 'b': 2, 'c':3}, 'a', 'c')
            >>> {'a': 1, 'c': 3}
    """
    filters = keys
    if isinstance(keys[0], list):
        filters = keys[0]
    return {k: v for k, v in _dict.items() if k in filters}

def in_both(d1: dict, d2: dict) -> list:
    """ Return the intersecting keys between two dictionaries """
    keys = [*d1.keys(), *d2.keys()]
    return set([key for key in keys if key in d1 and key in d2])

def save_csv(_dict: dict, name: str, dir_name="", output_dir=DATA_PATH) -> None:
    """ 
    Saves a dict into a csv 

    Args:
        _dict (dict): The dictionary that will be written or appended in the file
        name (str): The name of the file
        dir_name (str): Subdirectory inside .config.DATA_PATH that the file will be saved

    Raises:
        ValueError 
            if `dir_name` type isn't string 
    """
    filename = "%s.csv" % name

    if dir_name and not isinstance(dir_name, str):
        raise ValueError("Expected str instead of %s" % type(dir_name))
    elif dir_name and isinstance(dir_name, str):
        output_dir = output_dir.joinpath(dir_name)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_dir = join(output_dir, filename)

    mode = "a"

    if not isfile(output_dir):
        mode = "w"

    with open(output_dir, mode=mode, newline="") as f:
        writer = DictWriter(f, _dict.keys())

        if mode == "w":
            writer.writeheader()

        writer.writerow(_dict)


def diff_list(l1: List[Any], l2: List[Any]) -> List[Any]:
    return list(set(l1) ^ set(l2))