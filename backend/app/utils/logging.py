import logging
import sys
import time
from contextlib import contextmanager

# Configure structured formatter
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

def setup_logger(name: str = "ragify") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger("ragify")

@contextmanager
def log_latency(operation_name: str, extra_info: str = ""):
    """Context manager to measure and log operation latency."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        info_suffix = f" [{extra_info}]" if extra_info else ""
        logger.info(f"⏱️  {operation_name} completed in {elapsed_ms:.2f}ms{info_suffix}")
