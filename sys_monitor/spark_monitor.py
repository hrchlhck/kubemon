from requests.exceptions import ConnectionError
from requests import get, post
from time import sleep
import json

def join(url, *pages):
    for page in map(str, pages):
        url += "/" + page
    return url


def load_json(url):
    return json.loads(get(url).text)


class SparkMonitor:
    def __init__(self, addr, port, url="localhost:4040"):
        self.__url = "http://" + url + "/api/v1/applications"
        self.__app_id = self.__get_app_id()
        self.__addr = "http://" + addr + ":" + port

    def __get_app_id(self):
        """ Get Spark app ID Path -> <ip>:<port>/api/v1/applications/ """
        return load_json(join(self.__url, self.__app_id))[0]["id"]

    def __get_stage_info(self):
        """ Get stage info of app Path -> <ip>:<port>/api/v1/applications/<app_id>/stages/<stage_id> """
        stage_id = load_json(join(self.__url, self.__app_id, "stages"))[1]["stageId"]
        return load_json(join(self.__url, self.__app_id, "stages", stage_id))

    def __get_executors_info(self):
        """ Get stage info of app Path -> <ip>:<port>/api/v1/applications/<app_id>/allexecutors """
        return load_json(join(self.__url, self.__app_id, "allexecutors"))

    def __get_data(self):
        stage_data = self.__get_stage_info()[0]
        executors_data = stage_data["executorSummary"]["driver"]
        
        total_cpu_time = stage_data["executorCpuTime"]
        input_bytes = executors_data["inputBytes"]
        input_records = executors_data["inputRecords"]
        output_bytes = executors_data["outputBytes"]
        output_records = executors_data["outputRecords"]
        memory_used = executors_data["memoryUsed"]
        
        return {
            "total_cpu_time": total_cpu_time,
            "input_bytes": input_bytes,
            "input_records": input_records,
            "output_bytes": output_bytes,
            "output_records": output_records,
            "memory_used": memory_used
        }

    def __calc(self):
        data = self.__get_data()
        
        cpu = data["total_cpu_time"]
        input_bytes = data["input_bytes"]
        input_records = data["input_records"]
        output_bytes = data["output_bytes"]
        output_records = data["output_records"]
        memory_used = data["memory_used"]
        
        sleep(5)
        
        data = self.__get_data()
        cpu_new = data["total_cpu_time"]
        input_bytes_new = data["input_bytes"]
        input_records_new = data["input_records"]
        output_bytes_new = data["output_bytes"]
        output_records_new = data["output_records"]
        memory_used_new = data["memory_used"]
        
        cpu = round(cpu_new - cpu, 4)
        input_bytes = round(input_bytes_new - input_bytes, 4)
        input_records = round(input_records_new - input_records, 4)
        output_bytes = round(output_bytes_new - output_bytes, 4)
        output_records = round(output_records_new - output_records, 4)
        memory_used = round(memory_used_new - memory_used, 4)
        
        return (cpu, input_bytes, input_records, output_bytes, output_records, memory_used)

    def start(self):
        header = {"from": "spark_monitor"}
        
        while True:
            calc = self.__calc()
            data = {
                "total_cpu_time": calc[0],
                "input_bytes": calc[1],
                "input_records": calc[2],
                "output_bytes": calc[3],
                "output_records": calc[4],
                "memory_used": calc[5]
            }
            
            try:
                post(self.__addr, json=json.dumps(data), headers=header)
            except ConnectionError:
                print('Connection refused.')
