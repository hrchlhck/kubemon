from typing import List

def parse_fields(data: List[List[str]]) -> dict:
    """
        Parse fields on cgroups files or any file that contains the following pattern:

        input -> [[str int],
                    [str int],
                    [str int],
                    ...]
        output -> {str: int, str: int, str: int, ...}
        
        Args:
            data (list): List of lists representing a pair of data
    """
    to_int = lambda x: int(x) if x.isdigit() else x
    data = list(map(lambda x: x.replace('\n', '').split(), data))
    field_count = list(filter(lambda x: len(x) > 2, data))

    # Checking columns to avoid dict exceptions
    if len(field_count) >= 1:
        ret = list(map(lambda x: tuple(map(to_int, x)), data))
    else:
        ret = {k: to_int(v) for k, v in data}

    return ret

def _load_metrics(path: str) -> list:
    try:
        with open(path, mode='r') as fd:
            return parse_fields(list(fd))
    except FileNotFoundError:
        return list()