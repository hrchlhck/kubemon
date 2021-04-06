from sys_monitor import Disk
from re import findall
import unittest


class TestDisk(unittest.TestCase):
    def setUp(self):
        self.disk = Disk('sda', _disk_stat_path="./tests/resources/data/diskstats")
        self.infos = ['read_io',
                 'read_merge',
                 'read_sectors',
                 'read_ticks',
                 'write_io',
                 'write_merge',
                 'write_sectors',
                 'write_ticks',
                 'in_flight',
                 'io_ticks',
                 'time_in_queue',
                 'discard_io',
                 'discard_merges',
                 'discard_sectors',
                 'discard_ticks']

    def test_name(self):
        self.assertEqual(self.disk.name, 'sda')

    def test_major(self):
        self.assertEqual(self.disk.major, 8)
    
    def test_minor(self):
        self.assertEqual(self.disk.minor, 0)

    def test_partitions(self):
        self.assertEqual(len(list(self.disk._Disk__get_partitions())), 2)

    def test_partition_name(self):
        print(self.disk.get_usage(partition='sdb'))
        self.assertEqual(self.disk.get_usage(
            partition='sdb').name, 'sdb')

    def get_data(self, partition):
        with open('/sys/block/%s/stat' % partition, mode='r') as f:
            data = findall(r"\d+", f.readlines()[0])
            data = list(map(int, data))
        return data

    def compare_values(self, partition_obj, system_value):
        for i, info in enumerate(self.infos):
            if partition_obj[info] != system_value[i]:
                yield False
            else:
                yield True

    def test_partition_values(self):
        errors = 0
        partition = 'sda'
        partition_obj = self.disk.get_usage(partition=partition)
        data = self.get_data(partition)
        comparisons = self.compare_values(partition_obj, data)
        
        if False in comparisons:
            errors += 1

        self.assertEqual(errors, 0)

    def test_all_partition_values(self):
        errors = 0

        for partition in self.disk.get_usage(all_partitions=True):
            print("Testing partition %s" % partition)
            data = self.get_data(partition.name)
            comparisons = list(self.compare_values(partition, data))

            if False in comparisons: 
                errors += 1
        
        self.assertEqual(errors, 0)
    
    def test_sector_size(self):
        self.sectors = self.disk.sector_size
        self.assertEqual(512, self.sectors)




if __name__ == '__main__':
    unittest.main()
