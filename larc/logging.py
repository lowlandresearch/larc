import coloredlogs
from toolz import merge

def setup_logging(loglevel: str, **config_kw):
    fmt = (
        '{asctime} {levelname: <6} [{name}:{lineno: >4}]  {message}'
    )
    datefmt = '%Y-%m-%d %H:%M:%S'
    kw = merge({
        'level': loglevel.upper(),
        'datefmt': datefmt,
        'fmt': fmt,
        'style': '{',
    }, config_kw)
    coloredlogs.install(**kw)

