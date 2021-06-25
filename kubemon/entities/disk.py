from .base_entity import BaseEntity
from typing import List, Generator
import re


class Partition:
    """ Class for a simple representation of a disk partition on a Linux based system.
        For more information about the attributes, please refer to https://www.kernel.org/doc/html/latest/block/stat.html
    """

    def __init__(self, partition_name, rd_io, rd_merge, rd_sectors, rd_ticks, wt_io, wt_merge, wt_sectors, wt_ticks, in_flight, io_ticks, time_in_queue, ds_io, ds_merges, ds_sectors, ds_ticks, flush_io=0, flush_ticks=0):
        self.__partition_name = partition_name
        self.__info = {
            'read_io': rd_io,
            'read_merge': rd_merge,
            'read_sectors': rd_sectors,
            'read_ticks': rd_ticks,
            'write_io': wt_io,
            'write_merge': wt_merge,
            'write_sectors': wt_sectors,
            'write_ticks': wt_ticks,
            'in_flight': in_flight,
            'io_ticks': io_ticks,
            'time_in_queue': time_in_queue,
            'discard_io': ds_io,
            'discard_merges': ds_merges,
            'discard_sectors': ds_sectors,
            'discard_ticks': ds_ticks,
        }

        if flush_io and flush_ticks:
            self.__info.update({"flush_io": flush_io, "flush_ticks": flush_ticks})

    @property
    def name(self):
        return self.__partition_name

    @property
    def infos(self):
        return self.__info

    def __getitem__(self, info):
        return self.__info[info]

    def __str__(self):
        return 'Partition<{}>'.format(self.name)

    def __repr__(self):
        return self.__str__()


class Disk(BaseEntity):
    """ Class for retrieving data about disk partitions from a Linux based system """

    def __init__(self, disk_name, _disk_stat_path="/proc/diskstats", _partition_path="/proc/partitions"):
        self.__name = disk_name
        self._disk_stat_path = _disk_stat_path
        self._partition_path = _partition_path
        self.__parse_device_driver()
        self.__sector_size = self.__parse_sector_bytes(disk_name)
        self.__partitions = tuple(self.__get_partitions())
        super(Disk, self).__init__()

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

    def __parse_device_driver(self):
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


    def __parse_sector_bytes(self, partition: str):
        """ Get disk sector size in bytes """
        with open(f"/sys/block/{partition}/queue/hw_sector_size", mode='r') as fd:
            return int(list(fd)[0])

    def get_usage(self, all_partitions=False, partition='sda') -> List[Partition]:
        """ Get information from a partition or from all available partitions started with 'sd' """
        ret = tuple(self.__usage_generator(all_partitions, partition))

        if not all_partitions:
            return ret[0]
        return ret

    def __usage_generator(self, all_partitions=False, partition='sda') -> Generator:
        """ Returns a generator for each partition """
        if not all_partitions:
            yield self.__parse_data(partition)
        else:
            for _partition in self.partitions:
                yield self.__parse_data(_partition)

    def __parse_data(self, partition_name: str) -> Partition:
        """ Parses /sys/block/<partition_name>/stat file and returns a 'Partition' object"""
        filename = "/sys/block/{}/stat".format(partition_name)
        with open(filename, "r") as f:
            data = re.findall(r"\d+", f.readlines()[0])
            data = list(map(int, data))
            return Partition(partition_name, *data)

    def __get_partitions(self, prefix='sd'):
        """ Yields every disk partition that contains 'sd' or any given prefix """
        is_sd = lambda x: prefix in x
        with open(self._partition_path, mode='r') as f:
            for line in f.readlines():
                res = tuple(filter(is_sd, line.split()))
                if res:
                    yield res[0]
