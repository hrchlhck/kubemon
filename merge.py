from pathlib import Path
from os.path import join
import pandas as pd
import sys
import re	

# Matches IP addresses with underscores 
p = re.compile(r"(_[0-9]+){4}")

def get_name(file, pattern):
    name = Path(file).name.split("/")[-1]
    return re.search(pattern, name).group(0)

def merge(f1, f2):
    global p
    name = get_name(f1, p)
    file_dir = Path(f1).parent

    f1 = pd.read_csv(f1, sep=',')
    f2 = pd.read_csv(f2, sep=',')
    df = f1.join(f2)
    
    df.to_csv(join(file_dir, f"merged{name}.csv"), index=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: merge.py file1.csv file2.csv")
        exit(1)
    merge(sys.argv[1], sys.argv[2])
