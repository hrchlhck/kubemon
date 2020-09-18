from ..exceptions.platform_exception import NotLinuxException
from platform import platform
import re


class Disk:
    def __init__(self):
        self.__check_os()

    def get_info(self):
        with open(self.__PATH, "r") as f:
            data = re.findall(r"\d+", data.readlines()[0])
            return {"sectors_read": data[3], "sectors_written": data[7]}

    def __check_os(self):
        if not "Linux" in platform():
            raise NotLinuxException()


# find sda device and match every value after
# "import re; f = open('/proc/diskstats', 'r'); print(re.findall(r'(?<=sda ).*\d', f.readlines()[9])); f.close()"
