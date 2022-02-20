from typing import Callable, Any
from functools import wraps

def wrap_exceptions(*exceptions):
    """     
    Decorator to wrap try/except from functions. 
    
    Args:
        exceptions (list): Exception objects wanted to handle
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                print(e)
                exit(-1)
        return wrapper
    return decorator

def _label_metrics(preffix: str, metrics: dict) -> dict:
    return {f'{preffix}_{k}': v for k, v in metrics.items()}

def label(preffix: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ret = func(*args, **kwargs)
            return _label_metrics(preffix, ret)
        return wrapper
    return decorator
