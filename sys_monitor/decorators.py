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