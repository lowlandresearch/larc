import sys
from pathlib import Path

from ..common import clipboard_paste

def get_input_content(inpath, clipboard=False):
    if inpath:
        content = Path(inpath).read_text()
    elif clipboard:
        content = clipboard_paste()
    else:
        content = sys.stdin.read()
    return content

