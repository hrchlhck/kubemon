import os
from kubemon.monitors.docker_monitor import DockerMonitor
from kubemon.monitors.monitor import OSMonitor
from kubemon.monitors.process_monitor import ProcessMonitor
from kubemon.utils.networking import _check_service
from kubemon.utils.data import diff_list

from kubemon.utils.monitors import list_monitors

import unittest
import os

class TestNetwork(unittest.TestCase):
    def test_check_service(self):
        service_name = 'MONITOR'
        self.assertFalse(_check_service(service_name))
    
    def test_check_service_exist(self):
        service_name = 'MONITOR'
        os.environ[service_name] = 'teste'

        self.assertTrue(_check_service(service_name))

class TestDaemon(unittest.TestCase):
    def test_modules(self):
        mods = list_monitors([DockerMonitor, OSMonitor, ProcessMonitor])

        self.assertEqual(mods, ['docker', 'os', 'process'])
    
    def test_modules_error(self):
        with self.assertRaises(TypeError):
            list_monitors([DockerMonitor, OSMonitor, str])
    
    def test_modules_empty(self):
        self.assertEqual(list_monitors([]), [])

class TestData(unittest.TestCase):
    def test_diff_lists(self):
        l1 = [1, 2, 3, 4]
        l2 = [1, 2, 3, 5]
        res = diff_list(l1, l2)

        self.assertEqual(res, [4, 5])
    
    def test_diff_lists_include(self):
        l1 = [1, 2, 3, 4]
        l2 = [1, 2, 3, 4, 5]
        res = diff_list(l1, l2)

        self.assertEqual(res, [5])

if __name__ == '__main__':
    unittest.main()