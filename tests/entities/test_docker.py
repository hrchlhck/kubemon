import unittest
from sys_monitor import DockerMonitor


class TestDockerMonitor(unittest.TestCase):
    def setUp(self):
        self.dm = DockerMonitor(address="", port=9999, kubernetes=False, stats_path="./tests/entities/data")

    def test_parse_key_value_fields(self):
        with open('./tests/entities/data/memory.stat', mode='r') as fd:
            data = list(fd)
        _in = DockerMonitor.parse_fields(data)
        out = {'cache': 0,
               'rss': 7569408,
               'rss_huge': 0,
               'shmem': 0,
               'mapped_file': 0,
               'dirty': 0,
               'writeback': 0,
               'swap': 0,
               'pgpgin': 3465,
               'pgpgout': 1596,
               'pgfault': 4587,
               'pgmajfault': 0,
               'inactive_anon': 0,
               'active_anon': 6217728,
               'inactive_file': 1081344,
               'active_file': 0,
               'unevictable': 0,
               'hierarchical_memory_limit': 8213827584,
               'hierarchical_memsw_limit': 9223372036854771712,
               'total_cache': 0,
               'total_rss': 7569408,
               'total_rss_huge': 0,
               'total_shmem': 0,
               'total_mapped_file': 0,
               'total_dirty': 0,
               'total_writeback': 0,
               'total_swap': 0,
               'total_pgpgin': 3465,
               'total_pgpgout': 1596,
               'total_pgfault': 4587,
               'total_pgmajfault': 0,
               'total_inactive_anon': 0,
               'total_active_anon': 6217728,
               'total_inactive_file': 1081344,
               'total_active_file': 0,
               'total_unevictable': 0}
        self.assertEqual(_in, out)

    def test_parse_n_values(self):
        with open('./tests/entities/data/blkio.throttle.io_service_bytes', mode='r') as fd:
            data = list(fd)
        _in = DockerMonitor.parse_fields(data)
        out = [('8:16', 'Read', 0),
               ('8:16', 'Write', 1769472),
               ('8:16', 'Sync', 1769472),
               ('8:16', 'Async', 0),
               ('8:16', 'Discard', 0),
               ('8:16', 'Total', 1769472),
               ('Total', 1769472)]
        self.assertEqual(_in, out)

    def test_disk_return(self):
        dsp = "./tests/resources/data/diskstats"
        data = self.dm.get_disk_usage(disk_name='sdb', _disk_stat_path=dsp)
        expected = {
            'Read': 0,
            'Write': 1769472,
            'Sync': 1769472,
            'Async': 0,
            'Discard': 0,
            'Total': 1769472,
            'sectors_written': int(1769472 / 512),
            'sectors_read': int(0 / 512)
        }
        self.assertEqual(data, expected)

    def test_cpuacct_stat_user(self):
        data = self.dm.get_cpu_times()
        self.assertEqual(data['user'], 362)

    def test_cpuacct_stat_system(self):
        data = self.dm.get_cpu_times()
        self.assertEqual(data['system'], 87)

    def test_memory_stat_cache(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['cache'], 0)

    def test_memory_stat_rss(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['rss'], 7569408)

    def test_memory_stat_mapped_file(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['mapped_file'], 0)

    def test_memory_stat_pgpgin(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['pgpgin'], 3465)

    def test_memory_stat_pgpgout(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['pgpgout'], 1596)

    def test_memory_stat_pgfault(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['pgfault'], 4587)

    def test_memory_stat_pgmajfault(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['pgmajfault'], 0)

    def test_memory_stat_active_anon(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['active_anon'], 6217728)

    def test_memory_stat_inactive_anon(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['inactive_anon'], 0)

    def test_memory_stat_active_file(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['active_file'], 0)

    def test_memory_stat_inactive_file(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['inactive_file'], 1081344)

    def test_memory_stat_unevictable(self):
        data = self.dm.get_memory_usage()
        self.assertEqual(data['unevictable'], 0)
