from .base_entity import BaseEntity
import re


class Disk(BaseEntity):
    """ Returns sectors written and read on disk of a Linux based system """
    def get_info(self):
        return self.__parse_data("/sys/block/sda/stat")

    def __parse_data(self, path):
        with open(path, "r") as f:
            data = re.findall(r"\d+", f.readlines()[0])
            return {"sectors_read": int(data[3]), "sectors_written": int(data[7])}
