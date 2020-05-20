import re
from pathlib import Path
import calendar

import jinja2
import toolz.curried as _

from .. import common as __
from .. import logging
from .. import images
from .. import markdown

log = logging.new_log(__name__)

@_.curry
def find_files(start, filename):
    start_path = Path(start).resolve()

    log.info(f'Finding image {filename}')
    if Path(start_path, filename).exists():
        path = Path(start_path, filename)
        log.info(f'   found: {path}')
        return [path]

    file_re = re.compile(
        filename.lower().replace('.', '\\.').replace('*', '.*')
    )
    log.info(f'   searching with re: {file_re.pattern}')

    paths = _.pipe(
        __.walk(start_path),
        filter(lambda p: file_re.search(p.name.lower())),
        _.partial(sorted, key=lambda p: p.name),
        tuple,
    )
    if not paths:
        log.error(
            f'Could not find any filenames meeting the search string'
            f' "{filename}" looking in directory: {start_path}'
        )
    return paths

def pluralize(number, singular='', plural='s'):
    if number == 1:
        return singular
    return plural

def md_to_html(text):
    return markdown.markdown(text)

def long_date(text):
    import datetime
    import dateutil.parser
    try:
        if isinstance(text, datetime.datetime):
            dt = text
        else:
            dt = dateutil.parser.parse(text)
        return dt.strftime('%B %d, %Y')
    except ValueError as error:
        log.error(
            'Error in long_date:\n'
            f'error: {error}\n'
            f'for text: {repr(text)}\n'
            'exception:', exc_info=True
        )

def year(text):
    return _.pipe(
        text,
        __.maybe_dt,
        __.deref('year'),
    )

def month(text):
    return _.pipe(
        text,
        __.maybe_dt,
        __.deref('month'),
        lambda m: calendar.month_name[m],
    )

def add_filters(env: jinja2.Environment):
    env.filters['pluralize'] = pluralize
    env.filters['md_to_html'] = md_to_html
    env.filters['long_date'] = long_date
    env.filters['year'] = year
    env.filters['month'] = month
    env.filters['b64encode'] = __.b64encode_str
    return env

@_.curry
def make_figure(im_type, filename, caption, images, *, style: dict = None):
    style = _.pipe(
        _.pipe(
            style.items(),
            __.vmap(lambda k, v: f"{k}: {v}"),
            ';'.join,
        ),
        'style="{}"'.format,
    ) if style else ''
    figure = {'type': im_type, 'filename': Path(filename).name,
              'search': filename, 'caption': caption,
              'images': images, 'style': style}
    return get_env().get_template('figure.html.j2').render(figure=figure)

@_.curry
def figure_function(im_type, bytes_function, caption, filename, start='.',
                    *, style: dict = None):
    return _.pipe(
        filename,
        find_files(start),
        map(bytes_function),
        map(__.b64encode_str),
        tuple,
        make_figure(im_type, filename, caption, style=style),
    )

png = figure_function('png', images.common.png_bytes)
jpeg = figure_function('jpeg', images.common.jpeg_bytes)

def table(data):
    return get_env().get_template('table.html.j2').render(data=data)

def add_functions(env: jinja2.Environment):
    env.globals['png'] = png
    env.globals['jpeg'] = jpeg
    env.globals['table'] = table
    return env

get_env = _.compose_left(
    jinja2.Environment,
    add_filters,
    add_functions,
)
