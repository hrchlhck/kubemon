from ..exceptions.platform_exception import NotLinuxException
from platform import platform


class BaseEntity:
    __platform = platform()

    def __init__(self):
        self.__check_os()

    def __check_os(self):
        if not "Linux" in self.__platform:
            raise NotLinuxException(
                f"Using {self.__platform} instead of any Linux based system."
            )
