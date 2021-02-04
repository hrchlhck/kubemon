from sys_monitor import CPU
from psutil import cpu_times
from time import sleep
import unittest


class TestCPU(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU()

    def get_load_avg(self):
        with open('/proc/loadavg', mode='r') as f:
            data = f.readlines()[0].split()
            data = data[:3]
            data = tuple(map(float, data))
        return data

    def test_busy_time(self):
        c = cpu_times()
        c = c.user + c.system + c.irq + c.softirq + c.nice 
        self.assertEqual(c, self.cpu.get_usage)

    def test_busy_time_with_sleep(self):
        c = cpu_times()
        c = c.user + c.system + c.irq + c.softirq + c.nice 
        sleep(5)
        self.assertNotEqual(round(c, 4), self.cpu.get_usage)

    def test_load_avg(self):
        self.assertEqual(self.cpu.get_loadavg, self.get_load_avg())

if __name__ == '__main__':
    unittest.main()