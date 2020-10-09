from operator import add
from functools import wraps
from pyspark import SparkContext, SparkConf
from time import perf_counter
import sys


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = perf_counter()
        r = func(*args, **kwargs)
        t1 = perf_counter() - t0
        print(f"Time elapsed: {t1:.4f}")
        return r
    return wrapper

class SparkTest(object):
    def __init__(self, app_name):
        self.__conf = SparkConf().setMaster("local").setAppName(app_name)
        self.__spark = SparkContext(conf=self.__conf)
    
    @timeit
    def word_count(self, file):
        lines = self.__spark.textFile(file).flatMap(lambda line: line.split(" "))
        counts = lines.map(lambda x: (x, 1)).reduceByKey(add)
        output = counts.collect()

        sort = [(word, count) for word, count in output]
        sort = sorted(sort, key=lambda x: x[:][1])
        print(f"Most used word: {sort[-1]}")
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: wordcount <file>", file=sys.stderr)
        sys.exit(-1)

    st = SparkTest("PythonWordCount")
    st.word_count(sys.argv[1])