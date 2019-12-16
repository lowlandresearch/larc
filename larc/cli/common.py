import sys
from pathlib import Path
import logging
from typing import Union

import click
from toolz.curried import curry

from ..common import clipboard_paste

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

@curry
def exit_with_msg(logger, msg):
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    logger.error(msg)
    raise click.Abort()

_exit_with_msg = exit_with_msg(log)

def get_input_content(inpath, clipboard=False):
    if inpath:
        content = Path(inpath).read_text()
    elif clipboard:
        content = clipboard_paste()
    else:
        content = sys.stdin.read()
    return content

def path_cb_or_stdin(inpath: Union[str, Path], clipboard: bool):
    if inpath:
        log.info(f'Getting input from path: {inpath}')
        return Path(inpath).read_text()
    elif clipboard:
        log.info('Getting input from clipboard...')
        return clipboard_paste()
    log.info('Getting input from stdin...')
    return sys.stdin.read()

def cb_or_stdin(clipboard):
    if clipboard:
        log.info('Getting input from clipboard...')
        return clipboard_paste()
    log.info('Getting input from stdin...')
    return sys.stdin.read()
