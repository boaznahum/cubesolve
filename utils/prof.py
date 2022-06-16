import time
from contextlib import contextmanager


@contextmanager
def w_prof(topic: str, prof=True):

    if not prof:

        yield None

    else:
        start = time.time_ns()
        try:
            yield None
        finally:
            end = time.time_ns()
            print(f"Profiling: {topic}: {(end-start) / 1e9}")