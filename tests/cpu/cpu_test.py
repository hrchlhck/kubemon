from requests import get
from operator import add
from functools import wraps
from pyspark.sql import SparkSession
from time import perf_counter

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = perf_counter()
        r = func(*args, **kwargs)
        t1 = perf_counter() - t0
        print(f"Time elapsed: {t1:.4f}")
        return r
    return wrapper 


@timeit
def word_count(spark, url):
    r = get(url).text
    lines = spark.read.text(url).rdd.map(lambda r: r[0])
    counts = lines.flatMap(lambda x: x.split('\n'))\
        .map(lambda x: (x, 1))\
        .reduceByKey(add)
    
    output = counts.collect()
    
    sort = [(word, count) for word, count in output]
    sort = sorted(sort, key=lambda x: x[:][1])
    print(f"Most used word: {sort[-1]}")

if __name__ == "__main__":
    spark = SparkSession\
        .builder\
        .appName("PythonWordCount")\
        .getOrCreate()
    
    word_count(spark, "https://raw.githubusercontent.com/mxw/grmr/master/src/finaltests/bible.txt")
    
    spark.stop()