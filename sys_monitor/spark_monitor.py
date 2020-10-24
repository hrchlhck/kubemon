from .utils import filter_dict, load_json, join, merge_dict, subtract_dicts
from requests import post
from threading import Thread, Lock
from time import sleep
from json import dumps


class SparkMonitor:
    def __init__(self, addr, port, url="localhost:4040", interval=5, check_interval=0.5):
        self.__url = f"http://{url}/api/v1/applications"
        self.__app_id = self.__get_app_id()
        self.__addr = f"http://{addr}:{port}"
        self.__header = {"from": "spark_monitor"}
        self.__interval = interval
        self.__check_interval = check_interval
        self.__mutex = Lock()
        self.__data = []

    def __get_app_id(self):
        """ Get Spark app ID Path -> <ip>:<port>/api/v1/applications/ """
        tmp = load_json(self.__url)
        return tmp[0]["id"] if tmp else []

    def __get_stage_info(self, _id=""):
        """ Get stage info of app Path -> <ip>:<port>/api/v1/applications/<app_id>/stages/<stage_id> """
        return load_json(join(self.__url, self.__app_id, "stages", _id))

    def __get_executors_info(self):
        """ Get stage info of app Path -> <ip>:<port>/api/v1/applications/<app_id>/allexecutors """
        return load_json(join(self.__url, self.__app_id, "allexecutors"))
            
    def __get_info(self, method):
        """ Applies an condition to a method and updates app_id if it is empty """
        if not self.__app_id:
            self.__app_id = self.__get_app_id()
        else:
            return method()

    def __check_api(self):
        while True:
            stage = self.__get_stage_info(self.__get_stage_info()[0]["stageId"])[0]
            executors = self.__get_executors_info()[0]
            status = stage["status"]
            print(status)
            sleep(self.__check_interval)
            
            if status == "ACTIVE":
               cpu = stage["executorCpuTime"]
               with self.__mutex:
                   print(cpu)
                   self.__cpu_usage.append(cpu)

    def __get_data(self):
        """ Retrieves data from Spark REST API as dictionary """
        filters = [
            "executorCpuTime", "totalShuffleWrite", "totalShuffleRead",
            "totalInputBytes", "memoryUsed", "totalGCTime"
        ]

        stage = self.__get_info(self.__get_stage_info)
        executors = self.__get_info(self.__get_executors_info)
        
        if stage or executors:
            stage = self.__get_info(self.__get_stage_info)
            executors = self.__get_info(self.__get_executors_info)
            
            changed_stages = filter_dict(stage[0], filters)
            changed_executors = filter_dict(executors[0], filters)

            print(changed_stages, changed_executors)

            sleep(self.__interval)

            stage = self.__get_info(self.__get_stage_info)
            executors = self.__get_info(self.__get_executors_info)

            changed_stages_new = filter_dict(stage[0], filters)
            changed_executors_new = filter_dict(executors[0], filters)

            changed_stages = subtract_dicts(changed_stages, changed_stages_new)
            changed_executors = subtract_dicts(changed_executors, changed_executors_new)
            return merge_dict(changed_stages, changed_executors)
        else:
            sleep(self.__interval)

    def start(self):
        """ Starts SparkMonitor and post retrieved data to collector.py """
        sleep(self.__interval)
        while True:
            data = self.__get_data()
            print(data)
            try:
                if data is not None:
                    post(self.__addr, json=dumps(
                        data), headers=self.__header)
            except:
                print("Connection refused. Retrying...")
