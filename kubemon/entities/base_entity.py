from kubemon.exceptions.platform_exception import NotLinuxException

from abc import abstractmethod, ABC
from platform import platform

class BaseEntity(ABC):
    """ 
    Base class to represent a hardware component e.g. CPU, Hard Disk, RAM memory, network interfaces, etc. 
    
    Currently it only supports Linux based operating systems. Besides that, it raises an exception when
    inherited classes attepmts to run on a Windows OS. 
    """
    
    __platform = platform()

    def __init__(self, monitor_type: str):
        self._monitor_type = monitor_type
        self.__check_os()

    @abstractmethod
    def get_usage(self):
        """ Abstract method """
    
    def __call__(self, *args):
        return self.get_usage(*args)

    def __check_os(self):
        if not "Linux" in self.__platform:
            raise NotLinuxException(
                f"Using {self.__platform} instead of any Linux based system."
            )
