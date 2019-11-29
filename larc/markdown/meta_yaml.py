from typing import Tuple
import logging

import markdown
from toolz.curried import merge

from .. import yaml

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

def meta_and_content(lines: list) -> Tuple[list]:
    '''Split markdown content lines into metadata lines and markdown
    content lines

    Example:

    >>> meta_and_content("""---
    ... a: 1
    ... b: 2
    ... ---
    ... Some **markdown**
    ... """.splitlines())
    (['a: 1', 'b: 2'], ['Some **markdown**'])

    '''
    if lines[0] != '---':
        return [], lines

    stripped = [l.strip() for l in lines]
    
    if '---' not in stripped:
        log.error('Metadata start block with no end block')
        return [], lines

    index = stripped[1:].index('---') + 1
    return lines[1:index], lines[index + 1:]

class MetaYamlPreprocessor(markdown.preprocessors.Preprocessor):
    """Preprocess markdown content with YAML metadata parsing.

    YAML block is delimited by '---' at start and '---' at end.

    """

    def run(self, lines: list) -> list:
        meta_lines, lines = meta_and_content(lines)

        if meta_lines:
            meta = yaml.load('\n'.join(meta_lines))
            if self.md.meta is not None:
                self.md.meta = merge(self.md.meta, meta)
            else:
                self.md.meta = meta
        return lines

class MetaYamlExtension(markdown.Extension):
    """Extension for parsing YAML metadata part with Python-Markdown."""

    def extendMarkdown(self, md: markdown.Markdown, *args, **kwargs):
        if not hasattr(md, 'meta'):
            md.meta = None
        md.preprocessors.register(
            MetaYamlPreprocessor(md), "meta_yaml", 100
        )

def makeExtension(*args, **kwargs):
    return MetaYamlExtension(*args, **kwargs)
