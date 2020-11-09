from pathlib import Path
from os.path import join
import pandas as pd
import re	

# Matches IP addresses with underscores 
pattern = re.compile(r"(_[0-9]+){4}")

def get_name(file, pattern):
    name = Path(file).name.split("/")[-1]
    parsed_name = re.search(pattern, name)
    
    if not parsed_name:
        return name.replace(".csv", "")
    return parsed_name.group(0)

def merge(f1, f2):
    global pattern
    name = get_name(f1, pattern)
    file_dir = Path(f1).parent

    f1 = pd.read_csv(f1, sep=',')
    f2 = pd.read_csv(f2, sep=',')
    df = f1.join(f2)
    
    df.to_csv(join(file_dir, f"merged{name}.csv"), index=False)
