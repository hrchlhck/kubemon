from kubemon.utils import get_default_nic
from .base_entity import BaseEntity
from psutil import net_io_counters as _net


class Network(BaseEntity):
    """ A simple object to return network usage """
    
    @property
    def get_usage(self):
        return self.__get_net_usage()

    def __get_net_usage(self):
        n = _net(pernic=True)[get_default_nic()]
        ret = {
            "bytes_sent": n.bytes_sent,
            "bytes_recv": n.bytes_recv,
            "packets_sent": n.packets_sent,
            "packets_recv": n.packets_recv,
        }
        return ret
