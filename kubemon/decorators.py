from typing import Callable, Any
from functools import wraps


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
