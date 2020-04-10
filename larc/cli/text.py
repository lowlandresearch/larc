'''Tools for dealing with text data
'''
from pathlib import Path
import sys

import jinja2
import click
from .. import common as __
import toolz.curried as _

from ..common import difflines, intlines

from .. import markdown

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
    _.pipe(
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
    _.pipe(
        intlines(
            Path(patha).expanduser().read_text(),
            Path(pathb).expanduser().read_text(),
        ),
        '\n'.join,
        print,
    )


@click.command(
    help=(
        'Transform text via parsing inline YAML'
        ' metadata and rendering as template through Jinja2'
    ),
)
@click.argument(
    'paths', nargs=-1,
)
def render_templates(paths):
    contents = _.pipe(
        paths,
        _.map(lambda p: Path(p).expanduser()),
        _.map(lambda p: p.read_text()),
        tuple,
    )

    if not contents:
        contents = [sys.stdin.read()]
    
    _.pipe(
        contents,
        _.map(markdown.meta_yaml.meta_and_content),
        __.vmap(lambda d, c: jinja2.Environment().from_string(c).render(**d)),
        _.map(_.do(print)),
        tuple,
    )
