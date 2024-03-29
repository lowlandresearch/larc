
from markdown.extensions import Extension
import xml.etree.ElementTree as etree
from markdown.inlinepatterns import LinkInlineProcessor, IMAGE_LINK_RE
from markdown.extensions.attr_list import AttrListTreeprocessor
import re

# CAPTION_RE = r'\!\[(?=[^\]])'
CAPTION_RE = IMAGE_LINK_RE

class ImageInlineProcessor(LinkInlineProcessor):

    def handleMatch(self, m, data):
        text, index, handled = self.getText(data, m.end(0))
        if not handled:
            return None, None, None

        src, title, index, handled = self.getLink(data, index)
        if not handled:
            return None, None, None

        fig = etree.Element('figure')
        fig.set('class', 'figure text-center d-block')
        img = etree.SubElement(fig, 'img')
        cap = etree.SubElement(fig, 'figcaption')
        cap.set('class', 'figure-caption')

        img.set('src', src)
        img.set('class', 'figure-img img-fluid')

        if title is not None:
            img.set("title", title)

        cap.text = text

        # if attr_list is enabled, put '{: xxx}' inside <figure> at end
        # so attr_list will see it
        if 'attr_list' in self.md.treeprocessors:
            # find attr_list curly braces
            curly = re.match(AttrListTreeprocessor.BASE_RE, data[index:])
            if curly:
                # img[-1].tail = '\n'
                # img[-1].tail += curly.group()
                # remove original '{: xxx}'
                index += curly.endpos

        return fig, m.start(0), index


class CaptionsExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.register(ImageInlineProcessor(CAPTION_RE, md), 'caption', 151)


def makeExtension(**kwargs):
    return CaptionsExtension(**kwargs)
