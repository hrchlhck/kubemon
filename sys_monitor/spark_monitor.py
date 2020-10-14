from requests import post
from time import sleep
from utils import filter_dict, load_json, join, merge_dict, subtract_dicts
import json


class SparkMonitor:
    def __init__(self, addr, port, url="localhost:4040", interval=5):
        self.__url = "http://" + url + "/api/v1/applications"
        self.__app_id = self.__get_app_id()
        self.__addr = f"http://{addr}:{port}"
        self.__header = {"from": "spark_monitor"}
        self.__interval = interval

    def __get_app_id(self):
        """ Get Spark app ID Path -> <ip>:<port>/api/v1/applications/ """
        tmp = load_json(self.__url)
        if len(tmp) != 0:
            return tmp[0]["appId"]

    def __get_stage_info(self):
        """ Get stage info of app Path -> <ip>:<port>/api/v1/applications/<app_id>/stages/ """
        return load_json(join(self.__url, self.__app_id, "stages"))

    def __get_executors_info(self):
        """ Get stage info of app Path -> <ip>:<port>/api/v1/applications/<app_id>/allexecutors """
        return load_json(join(self.__url, self.__app_id, "allexecutors"))

    def __get_data(self):
        """ Retrieves data from Spark REST API as dictionary """
        filters = [
            "executorCpuTime", "totalShuffleWrite", "totalShuffleRead",
            "totalInputBytes", "memoryUsed", "totalGCTime", "rddBlocks"
        ]

        if self.__get_stage_info() and self.__get_executors_info():
            changed_stages = filter_dict(self.__get_stage_info()[0], filters)
            changed_executors = filter_dict(self.__get_executors_info()[0],
                                            filters)

            sleep(self.__interval)

            changed_stages_new = filter_dict(self.__get_stage_info()[0],
                                             filters)
            changed_executors_new = filter_dict(self.__get_executors_info()[0],
                                                filters)

            changed_stages = subtract_dicts(changed_stages, changed_stages_new)
            changed_executors = subtract_dicts(changed_executors,
                                               changed_executors_new)
            return merge_dict(changed_stages, changed_executors)
        else:
            sleep(self.__interval)

    def start(self):
        """ Starts SparkMonitor and post retrieved data to collector.py """
        while True:
            data = self.__get_data()
            print(data)
            try:
                if data is not None:
                    post(self.__addr, json=json.dumps(
                        data), headers=self.__header)
            except:
                print("Connection refused. Retrying...")


if __name__ == '__main__':
    sm = SparkMonitor("0.0.0.0", 9822)
    sm.start()
