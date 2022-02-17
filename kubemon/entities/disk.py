from kubemon.metrics.disk import METRIC_FUNCTIONS
from kubemon.settings import Volatile
from .base_entity import BaseEntity

import psutil

Volatile.set_procfs(psutil.__name__)

class Disk(BaseEntity):
    """ Class for retrieving data about disk partitions from a Linux based system """

    def __init__(self, disk_name: str, *args, _disk_stat_path=f"{psutil.PROCFS_PATH}/diskstats", _partition_path=f"{psutil.PROCFS_PATH}/partitions"):
        self.__name = disk_name
        self._disk_stat_path = _disk_stat_path
        self._partition_path = _partition_path
        self._parse_device_driver()
        self.__sector_size = self._parse_sector_bytes(disk_name)
        self.__partitions = tuple(self._get_partitions(_partition_path))
        super(Disk, self).__init__(*args)

    @property
    def partitions(self):
        return self.__partitions

    @property
    def name(self):
        return self.__name

    @property
    def major(self):
        return self.__major
    
    @property
    def minor(self):
        return self.__minor
    
    @property
    def sector_size(self):
        return self.__sector_size
    
    def __str__(self):
        return f"Disk<maj={self.major}, min={self.minor}, name={self.name}>"
    
    def __repr__(self):
        return self.__str__()

    def get_usage(self, *args) -> dict:
        return METRIC_FUNCTIONS[self._monitor_type](*args)

    def _parse_sector_bytes(self, partition: str):
        """ Get disk sector size in bytes """
        with open(f"/sys/block/{partition}/queue/hw_sector_size", mode='r') as fd:
            return int(list(fd)[0])

    def _get_partitions(self, partition_path, prefix='sd'):
        """ Yields every disk partition that contains 'sd' or any given prefix """
        is_sd = lambda x: prefix in x
        with open(partition_path, mode='r') as f:
            lines = f.readlines()

        for line in lines:
            res = tuple(filter(is_sd, line.split()))
            if res:
                yield res[0]

    def _parse_device_driver(self):
        """ Parse device driver version """
        with open(self._disk_stat_path, mode='r') as fd:
            data = fd.readlines()
        
        # Split values from each line
        data = list(map(lambda x: x.split(), data))

        # Select only major, minor and name values
        data = list(map(lambda x: (int(x[0]), int(x[1]), x[2]), data))

        # Filter by device name
        data = list(filter(lambda x: x[2] == self.name, data))

        # Set values
        if data:
            self.__major = data[0][0]
            self.__minor = data[0][1]
