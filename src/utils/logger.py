import logging
import datetime


def log_setter(
        logger_name: str = __name__,
        file_name: str = "./src/data/call_log.log",
        format: str = "%(message)s"
):
    """For setting up multiple loggers."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(file_name)
    log_format = logging.Formatter(format)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)


log_setter(logger_name=__name__)
logger = logging.getLogger(__name__)


def log(func):
    # Offset for eastern time
    offset = datetime.timedelta(hours=-5)

    def wrapper(*args, **kwargs):
        called_at = datetime.datetime.now(datetime.timezone(offset))
        msg = f"{func.__name__}, {func.__module__}"
        logger.info(msg + " " * (80 - len(msg)) + f"[{called_at}]")
        res = func(*args, **kwargs)
        logger.info("")
        return res

    return wrapper
