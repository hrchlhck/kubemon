import abc
from typing import Dict

class BaseMonitor(abc.ABC):
    """ Abstract class for monitors. """

    @abc.abstractmethod
    def get_stats(self) -> Dict[str, dict]:
        """ Abstract method """