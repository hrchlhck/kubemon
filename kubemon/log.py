import logging

from .settings import LOG_PATH, LOGGING_LEVEL

__all__ = ['create_logger']

def create_logger(name: str, level=LOGGING_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name)

    logger.setLevel(level)

    formatter = logging.Formatter("[%(asctime)s] | %(levelname)s | [%(filename)s:%(lineno)s - %(funcName)10s()] | Logger %(name)s -> %(message)s")

    fh = logging.FileHandler(LOG_PATH.joinpath(f'{name}.log'), mode='a+')
    sh = logging.StreamHandler()
    
    fh.setLevel(level)
    sh.setLevel(level)

    fh.setFormatter(formatter)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    return logger
