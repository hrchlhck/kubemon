from kubemon.metrics.cpu import METRIC_FUNCTIONS
from .base_entity import BaseEntity

class CPU(BaseEntity):
    """ Represents an CPU object that returns CPU usage of a system """

    def get_usage(self, *args):
        return METRIC_FUNCTIONS[self._monitor_type](*args)
