import pandas as pd
import sys

def merge(f1, f2):
    f1 = pd.read_csv(f1, sep=',')
    f2 = pd.read_csv(f2, sep=',')
    df = f1.join(f2)
    df.to_csv(f"merged_{f1.replace('.csv', '')}_{f2.replace('.csv', '')}.csv", index=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: main.py file1.csv file2.csv")
        exit(1)
    merge(sys.argv[1], sys.argv[2])