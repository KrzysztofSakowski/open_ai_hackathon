import time
import random
from functools import wraps


def exponential_backoff(max_retries=5, base_delay=1, max_delay=60, jitter=True):
    """
    Decorator that implements exponential backoff for retrying functions that may fail.

    Args:
        max_retries (int): Maximum number of retry attempts before giving up
        base_delay (float): Initial delay between retries in seconds
        max_delay (float): Maximum delay between retries in seconds
        jitter (bool): Whether to add random jitter to the delay time

    Returns:
        The decorated function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        raise Exception(f"Failed after {max_retries} retries: {str(e)}")

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** (retries - 1)), max_delay)

                    # Add jitter if enabled (helps prevent thundering herd problem)
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    print(f"{e} occurred. Retry {retries}/{max_retries} after {delay:.2f}s delay")
                    time.sleep(delay)

        return wrapper

    return decorator
