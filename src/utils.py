import time
import logging
from functools import wraps

def timing_decorator(func):
    """Decorator to measure execution time of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def validate_question(question: str) -> bool:
    """Validate that the question is a proper string."""
    if not isinstance(question, str):
        return False
    if len(question.strip()) < 3:
        return False
    return True
