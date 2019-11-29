'''Tools for dealing with text data
'''
from pathlib import Path

import click
from toolz.curried import pipe

from ..common import difflines, intlines

@click.command(
    help=('Given PATHA and PATHB of text, print difference (A-B)'),
)
@click.argument(
    'patha',
    type=click.Path(exists=True),
)
@click.argument(
    'pathb',
    type=click.Path(exists=True),
)
def diff_lines(patha, pathb):
    pipe(
        difflines(
            Path(patha).expanduser().read_text(),
            Path(pathb).expanduser().read_text(),
        ),
        '\n'.join,
        print,
    )

@click.command(
    help=('Given PATHA and PATHB of text, print intersection (A & B)'),
)
@click.argument(
    'patha',
    type=click.Path(exists=True),
)
@click.argument(
    'pathb',
    type=click.Path(exists=True),
)
def int_lines(patha, pathb):
    pipe(
        intlines(
            Path(patha).expanduser().read_text(),
            Path(pathb).expanduser().read_text(),
        ),
        '\n'.join,
        print,
    )

