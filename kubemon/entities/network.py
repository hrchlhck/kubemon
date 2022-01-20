from .base_entity import BaseEntity
from psutil import net_io_counters, net_connections


class Network(BaseEntity):
    """ A simple object to return network usage """
    
    @property
    def get_usage(self):
        return self.__get_net_usage()

    def __get_net_usage(self):
        n = net_io_counters()
        nc = net_connections(kind='all')
        ret = {
            **n._asdict(),
            "num_connections": len(nc),
        }
        return ret
