from typing import List, Type

from kubemon.monitors.base import BaseMonitor

def list_monitors(type_list: List[Type]) -> List[str]:
    """ Returns the abbreviation of the monitor name """

    if not len(type_list):
        return list()

    if any(i for i in type_list if not issubclass(i, BaseMonitor)):
        not_subclass = [type(i).__name__ for i in type_list if not issubclass(i, BaseMonitor)]
        raise TypeError(f'Must specify a \'BaseMonitor\' inherited class instead of \'{not_subclass}\'')
    
    return [i._type for i in type_list]