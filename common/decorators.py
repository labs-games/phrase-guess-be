from functools import wraps
from typing import Callable
from common.logger import log


def retry_on_error(no_of_retry: int = 3) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            retry_count: int = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log.exception("%s|retry_count=%s|error=%s", func.__name__, retry_count, e)
                    if retry_count < no_of_retry:
                        retry_count += 1
                    else:
                        raise e

        return wrapped_func

    return decorator
