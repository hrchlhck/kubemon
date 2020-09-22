from .base_entity import BaseEntity
import re


class Disk(BaseEntity):
    def get_info(self):
        return self.__parse_data("/sys/block/sda/stat")

    def __parse_data(self, path):
        with open(path, "r") as f:
            data = re.findall(r"\d+", data.readlines()[0])
            return {"sectors_read": data[3], "sectors_written": data[7]}
