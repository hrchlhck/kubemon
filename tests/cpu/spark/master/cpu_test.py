from operator import add
from functools import wraps
from pyspark import SparkContext
from random import random
from time import perf_counter, time, sleep


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
    def __init__(self):
        self.__spark = SparkContext().getOrCreate()

    @timeit
    def word_count(self):
        lines = self.__spark.textFile("/bible.txt").repartition(6)
        
        while True:
            counts = lines.flatMap(lambda x: x.split(' ')) \
                      .map(lambda x: (x, 1)) \
                      .reduceByKey(add)
            output = counts.collect()

    @timeit
    def pi(self):
        partitions = 18
        n = 100000 * 50000

        def f(_):
            x = random() * 2 - 1
            y = random() * 2 - 1
            return 1 if x ** 2 + y ** 2 <= 1 else 0

        count = self.__spark.parallelize(
            range(1, n + 1), partitions).map(f).reduce(add)

    def start(self):
        self.pi()
        # self.word_count()

    def this(self):
        return self.__spark


if __name__ == "__main__":
    try:
        st = SparkTest().start()
    except KeyboardInterrupt:
        st.this().stop()
