import sys
from functools import wraps
from .colors import *
from .temps import AXIS_NAMES


def _progressbar(it, prefix="", size=60, out=sys.stdout):  # Python3.6+
    count = len(it)

    def show(j):
        x = int(size * j / count)
        print(f"{prefix}{u'█' * x}{('.' * (size - x))} {j}/{count}", end='\r', file=out, flush=True)

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    print("\n", flush=True, file=out)


def kwargsmap(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        func_kwargs = {}
        varnames = list(func.__code__.co_varnames)
        try:
            varnames.remove('self')
        except:
            pass
        for k in varnames:
            try:
                func_kwargs[k] = kwargs[k]
            except:
                continue

        return func(*args, **func_kwargs)

    return wrap


def kwargsmaps(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        func_kwargs = {}
        varnames = list(func.__code__.co_varnames)

        for k in varnames:
            try:
                func_kwargs[k] = kwargs[k]
            except:
                continue

        return func(*args, **func_kwargs)

    return wrap


def progressbar(prefix="", size=60, out=sys.stdout):  # Python3.6+

    def wrap_iter_func(func):
        def wrap(*args, **kwargs):
            it = func(*args, **kwargs)
            count = len(it)

            def show(j):
                x = int(size * j / count)
                print(f"{prefix}{u'█' * x}{('.' * (size - x))} {j}/{count}", end='\r', file=out, flush=True)

            show(0)
            for i, item in enumerate(it):
                yield item
                show(i + 1)
            print("\n", flush=True, file=out)
            return it

        return wrap

    return wrap_iter_func
