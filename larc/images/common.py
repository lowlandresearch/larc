import io
import logging
from functools import wraps
from pathlib import Path
import typing as T

from pkg_resources import resource_filename
import toolz.curried as _
from multipledispatch import dispatch
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)

from .. import common as __
from ..logging import new_log

log = new_log(__name__)

BLUE = (87, 116, 160, 255)
BLUE2 = (100, 140, 200, 255)
GREY = (100, 100, 100, 255)

@dispatch((str, Path))
def jpeg_bytes(path: T.Union[str, Path]):
    return jpeg_bytes(Image.open(path))

@dispatch(Image.Image)          # noqa
def jpeg_bytes(image: Image.Image):
    buf = io.BytesIO()
    image.convert('RGB').save(buf, 'jpeg', optimize=True)
    return buf.getvalue()

@dispatch((str, Path))
def png_bytes(path: T.Union[str, Path]):
    return png_bytes(Image.open(path))

@dispatch(Image.Image)          # noqa
def png_bytes(image: Image.Image):
    buf = io.BytesIO()
    image.save(buf, 'png')
    return buf.getvalue()

def delta_point(x, y):
    def delta(dx=0, dy=0):
        return (x + dx, y + dy)
    return delta

def get_font(name):
    return resource_filename(__name__, f'templates/fonts/{name}')

def tt_font(path):
    def font(*a, **kw):
        return ImageFont.truetype(path, *a, **kw)
    return font

def cambria():
    fmap = _.pipe(
        [(frozenset(['italic', 'bold']), 'Cambria Bold Italic.ttf'),
         (frozenset(['bold']), 'Cambria Bold.ttf'),
         (frozenset(['italic']), 'Cambria Italic.ttf'),
         (frozenset(['math']), 'Cambria Math.ttf'),
         (frozenset(), 'Cambria.ttf')],
        _.map(lambda d: (d[0], tt_font(get_font(d[1])))),
        dict,
    )

    def font(*mods):
        return fmap[frozenset(mods)]
    return font

@_.curry
def draw_text(base_image: Image.Image, text: str, loc: T.Tuple[int, int], *,
              font_f: T.Callable = cambria, font_size: int = 20,
              mods: T.Iterable = None, size: T.Tuple[int, int] = None,
              fill: T.Union[str, T.Tuple[int, int, int]] = 'white'):
    overlay = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
    ovl_draw = ImageDraw.Draw(overlay)

    font = font_f()(*(mods or []))(font_size)
    loc = tuple(loc)

    draw_method = ovl_draw.text
    if '\n' in text:
        draw_method = ovl_draw.multiline_text
        
    draw_method(loc, text, font=font, fill=fill)

    final = Image.alpha_composite(base_image, overlay)

    if size:
        sx, sy = size
        w, h = final.size
        final = final.resize(
            (int(w * sx), int(h * sy)), resample=Image.LANCZOS
        )
        
    return final
