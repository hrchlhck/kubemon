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
            "bytes_sent": n.bytes_sent,
            "bytes_recv": n.bytes_recv,
            "packets_sent": n.packets_sent,
            "packets_recv": n.packets_recv,
            "dropin": n.dropin,
            "dropout": n.dropout,
            "errin": n.errin,
            "errout": n.errout,
            "num_connections": len(nc),
        }
        return ret
