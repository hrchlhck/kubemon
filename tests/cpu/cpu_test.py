from operator import add
from functools import wraps
from pyspark import SparkContext, SparkConf
from random import random
from time import perf_counter, sleep
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
        self.__conf = SparkConf()\
            .setMaster("local")\
            .setAppName(app_name)\
            .set("spark.executor.cores", "2")
        self.__spark = SparkContext(conf=self.__conf)
    
    @timeit
    def word_count(self, file):
        lines = self.__spark.textFile(file).flatMap(lambda line: line.split(" "))
        counts = lines.map(lambda x: (x, 1)).reduceByKey(add)
        output = counts.collect()

        sort = [(word, count) for word, count in output]
        sort = sorted(sort, key=lambda x: x[:][1])
        print(f"Most used word: {sort[-1]}")
        
        return counts
        
    @timeit
    def pi(self, partitions):
        n = 100000 * partitions

        def f(_):
            x = random() * 2 - 1
            y = random() * 2 - 1
            return 1 if x ** 2 + y ** 2 <= 1 else 0

        count = self.__spark.parallelize(range(1, n + 1), partitions).map(f).reduce(add)
        print("Pi is roughly %f" % (4.0 * count / n))
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: wordcount <file>", file=sys.stderr)
        sys.exit(-1)

    c = 0
    st = SparkTest("PythonWordCount")
    
    while True:
        st.word_count(sys.argv[1]).saveAsSequenceFile(f"data{c}.txt")
        st.pi(1000)
        sleep(5)
        c += 1