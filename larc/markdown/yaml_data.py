import re

import jinja2
import markdown
from toolz.curried import (
    pipe, complement, juxt, merge,
    interleave, partition, reduce, map,
)

from .. import yaml
from ..common import vmap, vcall, maybe_pipe, short_circuit

def monotonic(seq, cmp=lambda a, b: a <= b):
    return all(cmp(seq[i], seq[i + 1]) for i in range(0, len(seq) - 1))

class YamlDataError(ValueError):
    pass

start_re = re.compile(r'--yaml--', re.IGNORECASE)
end_re = re.compile(r'--endyaml--', re.IGNORECASE)

def not_enough_tags(lines):
    s, e = start_re.pattern, end_re.pattern
    return (
        lines.count(s) != lines.count(e),
        f'Start and end YAML tags do not agree: {s} start != {e} end'
    )

def start_indices(lines):
    return [i for i, l in enumerate(lines) if start_re.search(l)]

def end_indices(lines):
    return [i for i, l in enumerate(lines) if end_re.search(l)]

def all_indices(lines):
    return list(interleave(
        (start_indices(lines), end_indices(lines))
    ))

def not_correct_order(lines):
    valid = pipe(
        all_indices(lines),
        complement(monotonic),
    )
    return (
        valid, 'Start and end tags are not in the correct order.'
    )

def check_lines(lines):
    errors = [
        msg for boolean, msg in juxt(
            not_correct_order, not_enough_tags,
        )(lines) if boolean
    ]

    if errors:
        return False, '\n'.join(errors)
    return True, ''

def yaml_data(lines):
    def render(raw, data):
        return jinja2.Template(raw).render(**data)

    from toolz.curried import do
    
    return maybe_pipe(
        all_indices(lines),
        short_circuit(bool),  # catch null YAML early
        partition(2),
        vmap(lambda s, e: lines[s + 1:e]),
        map('\n'.join),
        map(yaml.load),
        merge,
        # lambda lines: '\n'.join(lines),
        # lambda raw: (raw, yaml.load(raw)),
        # vcall(render),
        # lambda raw: (raw, yaml.load(raw)),
        # vcall(render),
        # lambda data: data[1],
    ) or {}

def non_yaml_lines(lines):
    return pipe(
        [-1] + all_indices(lines) + [len(lines)],
        partition(2),
        vmap(lambda s, e: lines[s + 1:e]),
        reduce(lambda a, b: a + b)
    )

class YamlDataPreprocessor(markdown.preprocessors.Preprocessor):
    '''Parse out the YAML metadata blocks from the markdown

    A YAML metadata block:
    
    - Is delimited by:
        - a line `--yaml--` at the start
        - and a line `--endyaml--` at the end
    
    '''
    def run(self, lines):
        '''Parse YAML metadata blocks and store in self.markdown.metadata'''
        valid, msg = check_lines(lines)
        if not valid:
            raise YamlDataError(msg)

        meta = yaml_data(lines)
        if self.md.meta is not None:
            self.md.meta = merge(self.md.meta or {}, meta)
        else:
            self.md.meta = meta

        return non_yaml_lines(lines)


class YamlDataExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        if not hasattr(md, 'meta'):
            md.meta = None
        md.preprocessors.register(
            YamlDataPreprocessor(md), "yaml_data", 90
        )

def makeExtension(*args, **kwargs):
    return YamlDataExtension(*args, **kwargs)
