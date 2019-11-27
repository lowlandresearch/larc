import logging
import coloredlogs

def setup_logging(loglevel: str):
    level = logging.getLevelName(loglevel.upper())
    fmt = (
        '{asctime} {levelname: <8} [{name}]:{lineno: >4}: {message}'
    )
    datefmt = '%Y-%m-%d %H:%M:%S'
    coloredlogs.install(level=level)
    logging.basicConfig(level=level, datefmt=datefmt, format=fmt, style='{')

