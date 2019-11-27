from collections import namedtuple
import platform
import json
import encodings
import hashlib
import socket
import logging

from toolz.curried import (
    compose, pipe, map, first, concatv,
)

from .common import (
    Null,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

_py_attr = [
    'branch', 'build', 'compiler', 'implementation', 'revision', 'version'
]
_sig_attr = pipe(
    concatv(
        ['hostname', 'platform', 'architecture', 'machine', 'processor'],
        pipe(_py_attr, map(lambda a: f'python_{a}'), tuple),
    )
)
Signature = namedtuple('Signature', _sig_attr)

def host_signature():
    return Signature(
        socket.gethostname(),
        platform.platform(),
        platform.architecture(),
        platform.machine(),
        platform.processor(),
        *pipe(
            _py_attr,
            map(lambda a: f'python_{a}'),
            map(lambda a: getattr(platform, a)),
            map(lambda f: f()),
            tuple,
        ),
    )

def verify_signature_dict(sig):
    if not type(sig) is dict:
        log.error('Signature provided is not a dictionary')
        return False

    missing_keys = set(_sig_attr) - set(sig)
    if missing_keys:
        log.error(
            f'Signature missing keys: '
            f'{", ".join(sorted(missing_keys))}'
        )
        return False
    return True

def signature_from_dict(sig_dict):
    if not verify_signature_dict(sig_dict):
        return None
    return Signature(**sig_dict)
from_dict = signature_from_dict

def maybe_dict(t):
    try:
        return dict(t)
    except TypeError:
        return Null

def signature_from_tuple(sig_tuple):
    return pipe(
        sig_tuple,
        maybe_dict,
        signature_from_dict,
    )
from_tuple = signature_from_tuple

def signature_to_dict(sig):
    return sig._asdict()
to_dict = signature_to_dict

def signature_to_tuple(sig):
    return tuple(sig._asdict())
to_tuple = signature_to_tuple

utf8 = compose(first, encodings.utf_8.encode)

def signature_to_hash(sig):
    return pipe(
        sig,
        to_tuple,
        json.dumps,
        utf8,
        hashlib.sha512,
        lambda h: h.hexdigest(),
    )
to_hash = signature_to_hash
