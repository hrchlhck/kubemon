from sys_monitor import CPU
from psutil import cpu_times, cpu_stats
from time import sleep
import unittest


class TestCPU(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU()
        self.infos = ['cpu_stat_ctx_switches',
            'cpu_stat_interrupts',
            'cpu_stat_soft_interrupts',
            'cpu_stat_syscalls',
            'cpu_times_user',
            'cpu_times_system',
            'cpu_times_nice',
            'cpu_times_softirq',
            'cpu_times_irq',
            'cpu_times_iowait',
            'cpu_times_guest',
            'cpu_times_guest_nice',
            'cpu_times_idle']
        self.cpu_stats = cpu_stats()
        self.cpu_times = cpu_times()

    def test_sizes(self):
        self.assertEqual(len(self.cpu.get_usage), len(self.infos))

    def test_cpu_info_keys(self):
        errors = 0
        for k in self.infos:
            if k not in self.cpu.get_usage.keys():
                errors += 1
        self.assertEqual(errors, 0)
    
    def test_cpu_ctx_switches(self):
        self.assertEqual(self.cpu.get_usage.cpu_stat_ctx_switches, self.cpu_stats.ctx_switches)

    def test_cpu_interrupts(self):
        self.assertEqual(self.cpu.get_usage.cpu_stat_interrupts, self.cpu_stats.interrupts)

    def test_cpu_soft_interrupts(self):
        self.assertEqual(self.cpu.get_usage.cpu_stat_soft_interrupts, self.cpu_stats.soft_interrupts)

    def test_cpu_syscalls(self):
        self.assertEqual(self.cpu.get_usage.cpu_stat_syscalls, self.cpu_stats.syscalls)

    def test_cpu_time_system(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_system, self.cpu_times.system)

    def test_cpu_time_idle(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_idle, self.cpu_times.idle)

    def test_cpu_time_user(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_user, self.cpu_times.user)

    def test_cpu_time_guest(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_guest, self.cpu_times.guest)

    def test_cpu_time_iowait(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_iowait, self.cpu_times.iowait)

    def test_cpu_time_irq(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_irq, self.cpu_times.irq)

    def test_cpu_time_softirq(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_softirq, self.cpu_times.softirq)

    def test_cpu_time_nice(self):
        self.assertEqual(self.cpu.get_usage.cpu_times_nice, self.cpu_times.nice)


if __name__ == '__main__':
    unittest.main()