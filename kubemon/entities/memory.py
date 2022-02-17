from kubemon.metrics.memory import METRIC_FUNCTIONS
from .base_entity import BaseEntity

class Memory(BaseEntity):
    """ Represents an Memory object that returns Memory usage of a system """

    def get_usage(self, *args):
        return METRIC_FUNCTIONS[self._monitor_type](*args)
