from .utils import filter_dict, load_json, join_url, merge_dict, subtract_dicts
from threading import Thread, Lock
from requests import post
from socket import gethostname, gethostbyname
from time import sleep
from json import dumps


class SparkMonitor:
    def __init__(self, addr, port, url="spark-master:4040", interval=5, check_interval=.4):
        self.__url = f"http://{url}/api/v1/applications"
        self.__addr = f"http://{addr}:{port}"
        self.__header = {"from": "spark_monitor"}
        self.__interval = interval
        self.__check_interval = check_interval
        self.__mutex = Lock()
        self.__data = []
        self.__ip = gethostbyname(gethostname())
        self.__app_id = self.__get_app_id()

    def __get_app_id(self):
        """ Get Spark app ID 
        Path -> <ip>:<port>/api/v1/applications/
        """
        tmp = []
        try:
            tmp = load_json(self.__url)[0]["id"]
        except Exception as e:
            print(e)
        return tmp 

    def __get_stage_info(self):
        """ Get stage info of app 
            Path -> <ip>:<port>/api/v1/applications/<app_id>/stages/<stage_id>
        """
        return load_json(join_url(self.__url, self.__app_id, "stages"))

    def __get_executor_info(self):
        """ Get executor info based on worker IP
            Path -> <ip>:<port>/api/v1/applications/<app_id>/stages/<stage_id>
        """
        executors = load_json(join_url(self.__url, self.__app_id, "executors"))
        return list(filter(lambda executor: self.__ip in executor["hostPort"], executors))
            
    def __get_info(self, method):
        """ Applies an condition to a method and updates app_id if it is empty """
        if not self.__app_id:
            self.__app_id = self.__get_app_id()
        else:
            return method()

    def __get_cpu_usage(self):
        """ Checks the REST API provided by Spark and gets the CPU usage"""
        while True:
            try:
                stage = self.__get_stage_info()[1]
            
                status = stage["status"]
                if status == "ACTIVE":
                    cpu = stage["executorCpuTime"]
                    print(cpu)
                    if cpu:
                        with self.__mutex:
                            self.__data.append(cpu)
                sleep(self.__check_interval)
            except Exception as e:
                print(e, "getcpuusage")

    def __get_data(self):
        """ Retrieves data from Spark REST API as dictionary """
        filters = [
            "executorCpuTime", "totalShuffleWrite", "totalShuffleRead",
            "totalInputBytes", "memoryUsed", "totalGCTime"
        ]

        try:
            cpu_usage = 0   
            
            executor = filter_dict(self.__get_info(self.__get_executor_info)[0], filters)

            sleep(self.__interval)
            
            executor_new = filter_dict(self.__get_info(self.__get_executor_info)[0], filters)
            
            executor = subtract_dicts(executor, executor_new)
            
            cpu_usage = sum(set(self.__data)) / len(set(self.__data)) if self.__data else 0
            
            with self.__mutex:
                self.__data = []
            
            return merge_dict({"executorCpuTime": cpu_usage}, executor)
        except Exception as e:
            print(e)
        
    def start(self):
        """ Starts SparkMonitor and post retrieved data to collector.py """
        while not self.__app_id:
            sleep(0.1)
            self.__app_id = self.__get_app_id()

        t0 = Thread(target=self.__get_cpu_usage)
        t0.start()

        while True:
            data = self.__get_data()
            print(data)
            try:
                if data:
                    post(self.__addr, json=dumps(
                        data), headers=self.__header, timeout=0.8)
            except Exception as e:
                print(e)
                print("Connection refused. Retrying...")
