from kubemon.metrics.network import METRIC_FUNCTIONS
from .base_entity import BaseEntity

class Network(BaseEntity):
    """ A simple object to return network usage """
    
    def get_usage(self, *args):
        return METRIC_FUNCTIONS[self._monitor_type](*args)
