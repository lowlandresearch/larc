import concurrent.futures

from toolz.curried import (
    curry, concatv,
)
import gevent
import gevent.pool

from .common import vcall

@curry
def thread_map(func, iterable, *iterables, **tpe_kw):
    with concurrent.futures.ThreadPoolExecutor(**tpe_kw) as executor:
        for value in executor.map(func, *concatv((iterable,), *iterables)):
            yield value

@curry
def process_map(func, iterable, *iterables, **tpe_kw):
    with concurrent.futures.ProcessPoolExecutor(**tpe_kw) as executor:
        for value in executor.map(func, *concatv((iterable,), *iterables)):
            yield value

@curry
def thread_vmap(func, iterable, *iterables, **tpe_kw):
    yield from thread_map(vcall(func), iterable, *iterables, **tpe_kw)

@curry
def gevent_map(func, iterable, *iterables, max_workers=10):
    pool = gevent.pool.Pool(max_workers)
    return pool.map(func, *concatv((iterable,), *iterables))

@curry
def gevent_vmap(func, iterable, *iterables, max_workers=10):
    pool = gevent.pool.Pool(max_workers)
    return pool.map(vcall(func), *concatv((iterable,), *iterables))

def pmap(ptype: str):
    return {
        'thread': thread_map,
        'gevent': gevent_map,
    }.get(ptype, thread_map)
