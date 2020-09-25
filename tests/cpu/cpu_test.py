import sys
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
def word_count(spark, file):
    lines = spark.read.text(file).rdd.map(lambda r: r[0])
    counts = lines.flatMap(lambda x: x.split(' '))\
        .map(lambda x: (x, 1))\
        .reduceByKey(add)
    
    output = counts.collect()
    
    sort = [(word, count) for word, count in output]
    sort = sorted(sort, key=lambda x: x[:][1])
    print(sort)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: wordcound <file>", file=sys.stderr)
        sys.exit(-1)

    spark = SparkSession\
        .builder\
        .appName("PythonWordCount")\
        .getOrCreate()
    
    word_count(spark, sys.argv[1])
    
    spark.stop()