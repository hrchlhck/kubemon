from kubemon.settings import DATA_PATH

from functools import reduce
from pathlib import Path
from typing import Any, List

from csv import DictWriter

__all__ = ['subtract_dicts', 'merge_dict', 'filter_dict', 'in_both']

def subtract_dicts(dict1: dict, dict2: dict, operation=lambda x, y: x-y) -> dict:
    """ Subtracts values from dict1 and dict2 """
    if len(dict1) != len(dict2):
        missing_keys = set(dict1.keys()) ^ set(dict2.keys())
        raise KeyError(f"Mapping keys {missing_keys} not found")
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
    if not isinstance(d1, dict) or not isinstance(d2, dict):
        d = d1 if not isinstance(d1, dict) else d2
        raise TypeError(f'Expected dictionary instead of {type(d).__name__}')
    
    if not d1 and not d2:
        return list()

    return list(set(d1.keys()).intersection(d2.keys()))

def save_csv(_dict: dict, name: str, dir_name="", output_dir=DATA_PATH) -> None:
    """ 
    Saves a dict into a csv 

    Args:
        _dict (dict): The dictionary that will be written or appended in the file
        name (str): The name of the file
        dir_name (str): Subdirectory inside .settings.DATA_PATH that the file will be saved

    Raises:
        TypeError 
            if `dir_name` type isn't string 
    """
    filename = f"{name}.csv"

    if not isinstance(_dict, dict):
        raise TypeError(f'Expected a dictionary instead of {type(_dict).__name__}')
    
    if not isinstance(name, str):
        raise TypeError(f'Expected a string instead of {type(_dict).__name__}')

    if dir_name and not isinstance(dir_name, str):
        raise TypeError(f"Expected str instead of {type(dir_name).__name__}")
    elif dir_name and isinstance(dir_name, str):
        output_dir = output_dir / dir_name

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_dir = output_dir / filename

    write_header = False
    if not output_dir.exists():
        write_header = True

    with open(output_dir, mode='a+', newline="") as f:
        writer = DictWriter(f, _dict.keys())

        if write_header:
            writer.writeheader()

        writer.writerow(_dict)
