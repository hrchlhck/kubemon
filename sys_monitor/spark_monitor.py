from .utils import filter_dict, load_json, join, merge_dict, subtract_dicts
from subprocess import check_output
from threading import Thread, Lock
from requests import post
from socket import gethostname, gethostbyname
from time import sleep
from json import dumps


class SparkMonitor:
    def __init__(self, addr, port, url="spark-master:4040", interval=5, check_interval=0.5):
        self.__url = f"http://{url}/api/v1/applications"
        self.__addr = f"http://{addr}:{port}"
        self.__header = {"from": "spark_monitor"}
        self.__interval = interval
        self.__check_interval = check_interval
        self.__mutex = Lock()
        self.__data = []
        self.__ip = gethostbyname(gethostname())
        self.__app_ip = self.__get_app_id()

    def __get_app_id(self):
        """ Get Spark app ID 
        Path -> <ip>:<port>/api/v1/applications/
        """
        loop = True
        while loop:
            sleep(self.__check_interval)

            tmp = []
            try:
                tmp = load_json(self.__url)
            except Exception as e:
                print(e)

            if tmp:
                print("OK")
                loop = False
                return tmp[0]["id"]

    def __get_stage_info(self, _id=""):
        """ Get stage info of app 
            Path -> <ip>:<port>/api/v1/applications/<app_id>/stages/<stage_id>
        """
        return load_json(join(self.__url, self.__app_id, "stages", _id))

    def __get_executor_info(self):
        """ Get executor info based on worker IP
            Path -> <ip>:<port>/api/v1/applications/<app_id>/stages/<stage_id>
        """
        executors = load_json(join(self.__url, self.__app_id, "executors"))
        return list(filter(lambda executor: self.__ip in executor["hostPort"], executors))[0]
            
    def __get_info(self, method):
        """ Applies an condition to a method and updates app_id if it is empty """
        if not self.__app_id:
            self.__app_id = self.__get_app_id()
        else:
            return method()

    def __get_cpu_usage(self):
        """ Checks the REST API provided by Spark and gets the CPU usage"""
        while True:
            stage = self.__get_info(self.__get_stage_info)[0]
            status = stage["status"]
            sleep(self.__check_interval)
            if status == "ACTIVE":
               cpu = stage["executorCpuTime"]
               with self.__mutex:
                   print(cpu)
                   self.__data.append(cpu)

    def __get_data(self):
        """ Retrieves data from Spark REST API as dictionary """
        filters = [
            "executorCpuTime", "totalShuffleWrite", "totalShuffleRead",
            "totalInputBytes", "memoryUsed", "totalGCTime"
        ]

        cpu_usage = 0  
        
        executor = filter_dict(self.__get_info(self.__get_executor_info), filters)

        sleep(self.__interval)
        
        executor_new = filter_dict(self.__get_info(self.__get_executor_info), filters)
        
        executor = subtract_dicts(executor, executor_new)
        
        with self.__mutex:
            cpu_usage = sum(self.__data) / len(self.__data) if self.__data else 0
            self.__data = []
        return merge_dict({"executorCpuTime": cpu_usage}, executor)
        
    def start(self):
        """ Starts SparkMonitor and post retrieved data to collector.py """
        sleep(self.__interval)
        self.__app_id = self.__get_app_id()

        t0 = Thread(target=self.__get_cpu_usage)
        t0.start()
        
        while True:
            data = self.__get_data()
            print(data)
            try:
                if data:
                    post(self.__addr, json=dumps(
                        data), headers=self.__header)
            except:
                print("Connection refused. Retrying...")
