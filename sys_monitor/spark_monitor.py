from requests import get
import json

class SparkMonitor:
    def __init__(self, url):
        self.__url = "http://" + url + "/api/v1/applications"
        self.__app_id = self.__get_app_id()

    def __get_app_id(self):
        return json.loads(get(self.__url).text)[0]["id"]
    
    def get_stage_info(self):
        data = json.loads(get(self.__url + "/" + self.__app_id + "/stages").text)
        return [d for d in data if d["status"] != "COMPLETE"]

if __name__ == "__main__":
    sm = SparkMonitor("localhost:4040")
    print(sm.get_stage_info())