import logging
from pathlib import Path
from functools import wraps
import typing as T
from collections.abc import Mapping, Iterable

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap
from toolz import pipe
from multipledispatch import dispatch

from . import common

log = logging.getLogger('yaml')
log.addHandler(logging.NullHandler())

@wraps(ruamel.yaml.dump)
def dump(*a, **kw) -> str:
    kw['Dumper'] = ruamel.yaml.RoundTripDumper
    kw['default_flow_style'] = False
    kw['width'] = 2**31
    return ruamel.yaml.dump(*a, **kw)

@wraps(ruamel.yaml.load)
def load(*a, **kw) -> T.Any:
    kw['Loader'] = ruamel.yaml.RoundTripLoader
    return ruamel.yaml.load(*a, **kw)
    
def read_yaml(path: (str, Path)):
    '''Read YAML data from path and return object
    '''
    with Path(path).expanduser().open() as rfp:
        return load(rfp)

def maybe_read_yaml(path: (str, Path)):
    try:
        return read_yaml(path)
    except Exception:
        log.exception(f'Error reading YAML path: {path}')
        return common.Null

def _write_yaml(path, data):
    with Path(path).open('w') as wfp:
        dump(data, wfp)
    return True

@dispatch((str, Path), Mapping)
def write_yaml(path, dict_data):
    '''Write data as YAML to path

    Args:
      path (str, Path): path to write to

      data (dict-like): dictionary-like object to write (will be
         recursively converted to base Python types)

    Returns: (bool) success of write operation,

    Raises: on error, will raise exception

    '''
    return _write_yaml(path, pipe(dict_data,
                                  common.no_pyrsistent,
                                  CommentedMap))

@dispatch((str, Path), Iterable)  # noqa
def write_yaml(path, iterable_data):
    '''Write data as YAML to path

    Args:
      path (str, Path): path to write to

      data (sequence): sequence object to write (will be recursively
         converted to base Python types)

    Returns: (bool) success of write operation,

    Raises: on error, will raise exception

    '''
    return _write_yaml(path, pipe(iterable_data, common.no_pyrsistent))

@dispatch((str, Path), object)  # noqa
def write_yaml(path, object_data):
    return _write_yaml(path, object_data)

