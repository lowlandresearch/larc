import re
import logging

from markdown import Extension
from markdown.preprocessors import Preprocessor
from toolz.curried import (
    pipe, curry, merge, map, filter,
)

from ..common import (
    vmap, vfilter,
)
from .. import yaml

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

TABLE_RE = re.compile(r'^\s*\|==\[\[(?P<attrib>(.*?))\]\]==\|\s*$')
TH_RE = re.compile(
    r'^\s*(?:\[\[(?P<ra1>.*)\]\])?\s*\|=\s+(?P<th>(?:\S[\S ]*?\s+\|)+\s+\S[\S ]*?)\s+=\|\s*(?:\[\[(?P<ra2>.*)\]\])?\s*$'
)
TR_RE = re.compile(
    r'^\s*(?:\[\[(?P<ra1>.*)\]\])?\s*\|\|\s+(?P<tr>(?:\S[\S ]*?\s+\|)+\s+\S[\S ]*?)\s+\|\|\s*(?:\[\[(?P<ra2>.*)\]\])?\s*$'
)

ATTR_RE = re.compile(
    r'\s*(?:\[\[(?P<a>.*)\]\])\s*'
)

def attr_dict(s):
    return dict(yaml.load('{' + s + '}') if (s or '').strip() else {})

def attr_html(d):
    return pipe(
        d.items(),
        vmap(lambda k, v: f'{k}="{v}"'),
        ' '.join,
    )

def parse_tables(lines):
    table_lines = pipe(
        enumerate(lines),
        vmap(lambda i, l: (i, TABLE_RE.match(l))),
        vfilter(lambda i, m: m),
        tuple,
    )

    # log.debug(table_lines)

    ntables = 0

    for start_index, match in table_lines:
        table = {'start_index': start_index}
        log.debug(f'start index: {start_index}')
        attr = attr_dict(match.groupdict()['attrib'])
        table['caption'] = attr.pop('caption', '')
        table['attr'] = attr

        for i, line in enumerate(lines[start_index + 1:], start_index + 1):
            th_match = TH_RE.match(line)
            tr_match = TR_RE.match(line)
            if th_match:
                match_dict = th_match.groupdict()
                table['header'] = {
                    'line': i,
                    'tr': pipe(
                        th_match.groupdict()['th'].split('|'),
                        map(lambda s: s.strip()),
                        map(lambda s: (ATTR_RE.search(s),
                                       ATTR_RE.sub('', s))),
                        vmap(lambda m, s:
                             (merge(
                                 {'scope': 'col'},
                                 attr_dict(m.groupdict()['a']) if m else {},
                             ), s)),
                        vmap(lambda attr, td: {'td': td, 'attr': attr}),
                        tuple,
                    ),
                    'attr': pipe(
                        ['ra1', 'ra2'],
                        map(lambda k: match_dict.get(k, '')),
                        filter(None),
                        map(attr_dict),
                        merge,
                    ),
                }

            elif tr_match:
                match_dict = tr_match.groupdict()
                row = {
                    'line': i,
                    'tr': pipe(
                        match_dict['tr'].split('|'),
                        map(lambda s: s.strip()),
                        map(lambda s: (ATTR_RE.search(s),
                                       ATTR_RE.sub('', s))),
                        vmap(lambda m, s: (
                            attr_dict(m.groupdict()['a']) if m else {}, s
                        )),
                        vmap(lambda attr, td: {'attr': attr, 'td': td}),
                        tuple,
                    ),
                    'attr': pipe(
                        ['ra1', 'ra2'],
                        map(lambda k: match_dict.get(k, '')),
                        filter(None),
                        map(attr_dict),
                        merge,
                    )
                }

                table.setdefault('rows', []).append(row)

            else:
                # This is the case where we have gotten to a non-table
                # line of content, thus we are done with the table
                table['end_index'] = i
                log.debug(f'table end: {i}')
                ntables += 1
                yield table
                break
        
    if ntables < len(table_lines):
        # This is the case where the last line of content is a table
        # line
        log.debug('finishing table')
        table['end_index'] = i + 1
        yield table

@curry
def tr_to_html(data_tag: str, tr: dict):
    return (
        f'<tr {attr_html(tr.get("attr", {}))}>' + pipe(
            tr['tr'],
            map(lambda tr: (
                f'<{data_tag} {attr_html(tr["attr"])} >{tr["td"]}</{data_tag}>'
            )),
            ' '.join,
        ) + '</tr>'
    )

def table_to_html(lines):
    new_lines = lines[:]
    tables = list(parse_tables(lines))
    for table in tables:
        new_lines[table['start_index']] = (
            f'<table {attr_html(table["attr"])} > {table["caption"]}'
        )

        header = table.get('header', {})
        if header:
            new_lines[header['line']] = tr_to_html('th', header)

        for row in table.get('rows', []):
            new_lines[row['line']] = tr_to_html('td', row)

    end_indexes = [t['end_index'] for t in tables]
    for index in end_indexes[::-1]:
        new_lines.insert(index, '</table>')

    return new_lines

def tr_to_pandoc(tr):
    return (
        '| ' + pipe(
            tr['tr'],
            map(lambda tr: tr["td"]),
            ' | '.join,
        ) + ' |'
    )

def table_to_pandoc(lines):
    new_lines = lines[:]
    tables = list(parse_tables(lines))
    header_seps = []
    for table in tables:
        new_lines[table['start_index']] = ''
        header = table.get('header', {})
        if header:
            new_lines[header['line']] = tr_to_pandoc(header)

        if not (header or table['rows']):
            # We have a table start with neither a header or data
            # rows, so just skip and move on
            continue

        header_sep_index = (
            header['line'] if header else table['rows'][0]['line']
        ) + 1
        header_sep_length = (
            len(header['tr']) if header else len(table['rows'][0]['tr'])
        )
        header_seps.append((
            header_sep_index,
            '|' + '|'.join(['---'] * header_sep_length) + '|'
        ))

        for row in table.get('rows', []):
            new_lines[row['line']] = tr_to_pandoc(row)

    for index, sep in header_seps[::-1]:
        new_lines.insert(index, sep)
        
    return new_lines

class TablePreprocessor(Preprocessor):
    def run(self, lines):
        return table_to_html(lines)
            
class SimpleTableExtension(Extension):
    # def extendMarkdown(self, md, md_globals):
    def extendMarkdown(self, md):
        md.preprocessors.register(
            TablePreprocessor(md), "simpletable", 10
        )
        

def makeExtension(*args, **kwargs):
    return SimpleTableExtension(*args, **kwargs)

