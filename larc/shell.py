import os
import io
import sys
import subprocess
import shlex
import logging
from threading import Timer
from typing import Callable, Any, List
from pathlib import Path        # noqa: for doctest
import tempfile                 # noqa: for doctest

from toolz.curried import merge, map, pipe, curry
from toolz.curried import do

from .common import cprint

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

def start_timeout(command: List[str], process: subprocess.Popen,
                  timeout: int):
    # https://www.blog.pythonlibrary.org/2016/05/17/python-101-how-to-timeout-a-subprocess/
    def kill():
        log.warning(f'Process ({command[0]}) timeout expired.')
        return process.kill()
    timer = Timer(timeout, kill)
    timer.start()
    return timer

@curry
def shell_iter(command, *, echo: bool = True,
               echo_func: Callable[[Any], None] = cprint(file=sys.stderr,
                                                         end=''),
               timeout: int = None, **popen_kw):
    '''Execute a shell command, yield lines of output as they come
    possibly echoing command output to a given echo_func, and finally
    yields the status code of the process.

    This will run the shell command, yielding each line of output as
    it runs. When the process terminates, it will then yield the
    remainer of output, then finally the integer status code. It can
    also be terminated early via a timeout parameter. By default, the
    command will also echo to stderr.

    Args:

      command (str): Shell command to execute. Tilde (~) and shell
        variable completion provided

      echo (bool): Should the output be echoed to echo_func in
        addition to yielding lines of output?

      echo_func (Callable[[Any], None]): Function to use when echoing
        output. **Be warned**, this funciton is called __for each
        character__ of output. By default, this is `cprint(end='')`
        (i.e. print with end='')

      timeout (int): If set, the process will be killed after this
        many seconds (kill -9).

    Returns: generator of the form

        *output_lines, status_code = shell_iter(...)

      where output_lines is a sequence of strings of output and
      status_code is an integer status code

    Examples:

    >>> with tempfile.TemporaryDirectory() as tempdir:
    ...     root = Path(tempdir)
    ...     _ = Path(root, 'a.txt').write_text('')
    ...     _ = Path(root, 'b.txt').write_text('')
    ...     # FYI, this echos to stderr, which doctests won't capture
    ...     *lines, status = shell_iter(f'ls {root}')
    >>> lines
    ['a.txt', 'b.txt']
    >>> status
    0

    >>> with tempfile.TemporaryDirectory() as tempdir:
    ...     root = Path(tempdir)
    ...     _ = Path(root, 'c.txt').write_text('')
    ...     _ = Path(root, 'd.txt').write_text('')
    ...     *lines, _ = shell_iter(f'ls {root}', echo=False)
    >>> lines
    ['c.txt', 'd.txt']

    >>> *lines, status = shell_iter(
    ...     f'sleep 5', echo=False, timeout=0.01
    ... )
    >>> lines
    []
    >>> status
    -9

    '''
    popen_kw = merge({
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
    }, popen_kw)

    command_split = pipe(
        shlex.split(command),
        map(os.path.expanduser),
        map(os.path.expandvars),
        tuple,
    )

    process = subprocess.Popen(command_split, **popen_kw)

    timer = None
    if timeout:
        timer = start_timeout(command_split, process, timeout)

    def process_running():
        return process.poll() is None

    line = ''
    while process_running():
        char = process.stdout.read(1).decode('utf-8', errors='ignore')
        if char:
            echo_func(char) if echo else ''
            if char == '\n':
                yield line
                line = ''
            else:
                line += char

    if timer:
        timer.cancel()
        
    rest = process.stdout.read().decode('utf-8', errors='ignore')
    for char in rest:
        echo_func(char) if echo else ''
        if char == '\n':
            yield line
            line = ''
        else:
            line += char

    if line:
        echo_func(char) if echo else ''
        yield line

    yield process.poll()

@curry
def shell(command, **kw):
    '''Execute a shell command and return status code as an int and
    command output as a string, possibly echoing command output to a
    given echo_func.

    Args:

      command (str): Shell command to execute. Tilde (~) and shell
        variable completion provided

      echo (bool): Should the output be echoed to echo_func in
        addition to yielding lines of output?

      echo_func (Callable[[Any], None]): Function to use when echoing
        output. **Be warned**, this funciton is called __for each
        character__ of output. By default, this is `cprint(end='')`
        (i.e. print with end='')

      timeout (int): If set, the process will be killed after this
        many seconds (kill -9).

    Examples:

    >>> with tempfile.TemporaryDirectory() as tempdir:
    ...     root = Path(tempdir)
    ...     _ = Path(root, 'a.txt').write_text('')
    ...     _ = Path(root, 'b.txt').write_text('')
    ...     # FYI, this echos to stderr, which doctests won't capture
    ...     status, output = shell(f'ls {root}')
    >>> output == "a.txt\\nb.txt"
    True
    >>> status
    0

    >>> with tempfile.TemporaryDirectory() as tempdir:
    ...     root = Path(tempdir)
    ...     _ = Path(root, 'c.txt').write_text('')
    ...     _ = Path(root, 'd.txt').write_text('')
    ...     _, output = shell(f'ls {root}', echo=False)
    >>> output == 'c.txt\\nd.txt'
    True

    >>> status, output = shell(
    ...     f'sleep 5', echo=False, timeout=0.01
    ... )
    >>> output == ""
    True
    >>> status
    -9

    '''
    *lines, status = shell_iter(command, **kw)
    return status, '\n'.join(lines)

@curry
def getoutput(command, **kw):
    status, content = shell(command, **kw)
    return content


@curry
def shell_pipe(command, stdin, *, timeout: int = None, **popen_kw):
    '''Execute a shell command with stdin content and return command
    output as a string.

    Args:

      command (str): Shell command to execute. Tilde (~) and shell
        variable completion provided

      stdin (str): String content to provide to process stdin

      timeout (int): If set, the process will be killed after this
        many seconds (kill -9).

    Examples:

    >>> with tempfile.TemporaryDirectory() as tempdir:
    ...     root = Path(tempdir)
    ...     _ = Path(root, 'a.txt').write_text('')
    ...     _ = Path(root, 'b.txt').write_text('')
    ...     _ = Path(root, 'ab.txt').write_text('')
    ...     output = pipe(
    ...         getoutput(f'ls {root}'),
    ...         shell_pipe('grep a')
    ...     )
    >>> sorted(output.strip().split()) == ["a.txt", "ab.txt"]
    True

    '''
    popen_kw = merge({
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'stdin': subprocess.PIPE,
    }, popen_kw)

    command_split = pipe(
        shlex.split(command),
        map(os.path.expanduser),
        map(os.path.expandvars),
        tuple,
    )

    process = subprocess.Popen(command_split, **popen_kw)

    timer = None
    if timeout:
        timer = start_timeout()
    stdout, stderr = process.communicate(
        stdin.encode('utf-8', errors='ignore')
    )

    if timer:
        timer.cancel()

    return stdout.decode('utf-8', errors='ignore')
