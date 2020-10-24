from operator import add
from functools import wraps
from pyspark import SparkContext
from random import random
from time import perf_counter
from threading import Thread


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
    def word_count(self, file):
        lines = self.__spark.read.text(file).rdd.map(lambda r: r[0])
        counts = lines.flatMap(lambda x: x.split(' ')) \
                  .map(lambda x: (x, 1)) \
                  .reduceByKey(add)
        output = counts.collect()
        for (word, count) in output:
            print("%s: %i" % (word, count))

    @timeit
    def pi(self):
        partitions = 2 ** 16
        n = 100000 * partitions

        def f(_):
            x = random() * 2 - 1
            y = random() * 2 - 1
            return 1 if x ** 2 + y ** 2 <= 1 else 0

        count = self.__spark.parallelize(
            range(1, n + 1), partitions).map(f).reduce(add)
        print("Pi is roughly %f" % (4.0 * count / n))

    def start(self):
        t0 = Thread(target=self.pi, args=())
        # t1 = Thread(target=self.word_count, args=("/bible.txt"))
        
        t0.start()
        # t1.start()

    def this(self):
        return self.__spark


if __name__ == "__main__":
    try:
        st = SparkTest().start()
    except KeyboardInterrupt:
        st.this().stop()
