import re
from typing import List
import logging

import markdown
from markdown import Extension
from markdown.preprocessors import Preprocessor
from toolz.curried import (
    pipe, curry, merge, map, filter,
)

from .. import common
from .. import yaml

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

card_begin_re = re.compile(
    r'\|\.+(?:\[(?P<card_type>.*)\])?\.+\|'
)
card_end_re = re.compile(
    r'\|\^*\|'
)

def defcard(lines):
    return lines

def first_nonempty(lines):
    for i, l in enumerate(lines):
        if l.strip():
            return i, l

'''
  <div class="card mb-3 mt-3 vuln-card hideable">
    <div class="card-body finding-card-body">
      {% for dt, dd in rows %}
        <div class="row">
          <div class="col-4">{{ dt }}</div>
          <div class="col-8">{{ dd }}</div>
        </div>
      {% endfor %}
    </div>
  </div>
'''

def make_card(lines):
    hi, header = first_nonempty(lines[1:])
    hi += 1
    
    yield from [
        '<div class="card mb-2 mt-2">',
        '<div class="card-header">' + markdown.markdown(header) + '</div>',
        '<div class="card-body">',
    ] + lines[hi + 2:] + [
        '</div>',
        '</div>',
    ]

class ReMatchCase:
    def __init__(self):
        self.matchers = {}
        self._default = lambda value, *a, **kw: value

    def match(self, regex):
        def decorator(func):
            self.matchers[re.compile(regex)] = func
            return func
        return decorator

    def default(self, func):
        self._default = func
        return func

    def __call__(self, value, *a, **kw):
        for regex, func in self.matchers.items():
            match = regex.match(value)
            if match:
                return func(value, match, *a, **kw)
        return self._default(value, *a, **kw)

parse_header = ReMatchCase()

@parse_header.match(r'^(?P<header>#+)\s+(?P<text>.*?)\s*$')
def header_tag_header(_, match):
    mdict = match.groupdict()
    h_tag = f'h{len(mdict["header"])}'
    text = mdict['text'].strip()
    id_text = pipe(
        text.lower().split(),
        '-'.join,
    )
    return (
        # f'<a name={id_text} />'
        f'<{h_tag} class="card-header mdcard-header">{text}</{h_tag}>'
    )

@parse_header.default
def bare_text_header(header):
    text = markdown.markdown(header.strip())
    id_text = pipe(
        header.strip().lower().split(),
        '-'.join,
    )
    return (
        # f'<a name={id_text} />'
        f'<div class="card-header mdcard-header">{text}</div>'
    )

def card_to_html(lines: List[str]):
    new_lines = lines[:]

    delete = []
    for i, line in enumerate(new_lines):
        begin = card_begin_re.match(line)
        end = card_end_re.match(line)
        if begin:
            new_lines[i] = '<div class="card mb-2 mt-2 mdcard">'
            hi, header = first_nonempty(new_lines[i + 1:])
            hi += i + 1

            for i in range(i + 1, hi):
                if not new_lines[i].strip():
                    delete.append(i)

            new_lines[hi] = (
                parse_header(header) +
                # '<div class="card-header mdcard-header">' +
                # markdown.markdown(header.strip()) +
                '<div class="card-body mdcard-body">'
            )
        elif end:
            new_lines[i] = '</div></div>'
    for i in delete[::-1]:
        new_lines.pop(i)
    return new_lines

# def card_to_html(lines: List[str]):
#     new_lines = lines[:]

#     cards = []
#     for i, line in enumerate(new_lines):
#         begin = card_begin_re.match(line)
#         end = card_end_re.match(line)
#         if begin:
#             cards.append((i, begin))
#         elif end and cards:
#             (i0, begin) = cards.pop()
#             i1 = i
#             card_type = begin.groupdict()['card_type']
#             if card_type and card_type in globals():
#                 yield from globals()[card_type](lines[i0: i1])
#             else:
#                 yield from make_card(lines[i0: i1])
#         elif not cards:
#             yield line

class CardPreprocessor(Preprocessor):
    def run(self, lines):
        return list(card_to_html(lines))
            
class BootstrapCardExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(
            CardPreprocessor(md), "bootstrapcard", 8
        )
        
def makeExtension(*args, **kwargs):
    return BootstrapCardExtension(*args, **kwargs)

