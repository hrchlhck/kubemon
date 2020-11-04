from ..exceptions.platform_exception import NetworkInterfaceException
from .base_entity import BaseEntity
from psutil import net_io_counters as _net
from psutil import net_connections as nc


class Network(BaseEntity):
    """ A simple object to return network usage """
    def get_info(self):
        return self.__parse_data()

    def __parse_data(self):
        net = _net()

        d = {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv
        }

        return d
