from os.path import join, abspath
import pandas as pd
import sys

def merge(f1, f2):
    path = abspath(f1)
    f1 = pd.read_csv(f1, sep=',')
    f2 = pd.read_csv(f2, sep=',')
    df = f1.join(f2)
    df.to_csv(join("/".join(path.split("/")[0:-1]), "merged.csv"), index=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: merge.py file1.csv file2.csv")
        exit(1)
    merge(sys.argv[1], sys.argv[2])